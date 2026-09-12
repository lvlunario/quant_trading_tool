"""Synthetic normalized import contract; NOT a Fidelity CSV adapter.

Fail-closed reconciliation: any rejected row or unmatched account total
prevents publication of accepted positions. No persistence or broker access.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import re
from typing import Literal

from .risk import amount


@dataclass(frozen=True)
class ImportRow:
    account_alias: str
    asset_type: Literal['equity', 'cash', 'core_cash']
    symbol: str
    quantity: str
    price: str
    market_value: str


@dataclass(frozen=True)
class RowOutcome:
    row_number: int
    status: Literal['accepted', 'rejected']
    code: str


@dataclass(frozen=True)
class Reconciliation:
    status: Literal['reconciled', 'blocked']
    outcomes: tuple[RowOutcome, ...]
    errors: tuple[str, ...]
    rows: tuple[ImportRow, ...]
    account_totals: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class ImportEnvelope:
    schema_version: int
    mode: Literal['synthetic', 'user_export']
    currency: Literal['USD']
    source_type: Literal['normalized_synthetic', 'normalized_user_export']
    source_id: str
    as_of: datetime
    expected_totals: dict[str, str]
    rows: tuple[ImportRow, ...]


def _money(value: str) -> Decimal:
    # Bound input length/magnitude/scale so arithmetic remains exact and cheap.
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,15}(?:\.\d{1,8})?', value):
        raise ValueError('invalid_decimal')
    return amount(value)


def reconcile(rows: list[ImportRow], expected_totals: dict[str, str]) -> Reconciliation:
    """Validate normalized rows against independently supplied USD totals.

    Exact Decimal equality is intentional: adapters must explicitly resolve
    broker rounding rather than silently broadening a tolerance. Cash rows
    have blank symbol and quantity/price zero. At most one cash representation
    per account is accepted, preventing cash/core-fund double counting.
    All row outcomes are returned; raw values are never put in error messages.
    """
    if not isinstance(rows, list) or not rows or len(rows) > 10000:
        raise ValueError('invalid_row_count')
    if not isinstance(expected_totals, dict) or not expected_totals:
        raise ValueError('expected_totals_required')
    alias_pattern = r'ACCT_[A-Z]{1,16}'
    for alias in expected_totals:
        if not isinstance(alias, str) or not re.fullmatch(alias_pattern, alias):
            raise ValueError('invalid_account_alias')
    expected = {alias: _money(value) for alias, value in expected_totals.items()}
    keys = []
    for row in rows:
        if isinstance(row, ImportRow) and isinstance(row.account_alias, str) and isinstance(row.symbol, str):
            keys.append((row.account_alias, 'CASH' if row.asset_type in ('cash', 'core_cash') else row.symbol))
        else:
            keys.append(None)
    counts = Counter(key for key in keys if key is not None)
    outcomes, totals = [], {}
    with localcontext() as context:
        context.prec = 80
        for index, (row, key) in enumerate(zip(rows, keys), 1):
            code = 'ok'
            if not isinstance(row, ImportRow) or key is None:
                code = 'invalid_row'
            elif row.account_alias not in expected:
                code = 'unknown_account'
            elif row.asset_type not in ('equity', 'cash', 'core_cash'):
                code = 'unsupported_asset'
            elif counts[key] > 1:
                code = 'duplicate_position_or_cash'
            else:
                try:
                    quantity, price, value = map(_money, (row.quantity, row.price, row.market_value))
                    if row.asset_type == 'equity':
                        if not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,15}', row.symbol):
                            code = 'invalid_symbol'
                        elif quantity == 0 or price == 0:
                            code = 'nonpositive_position'
                        elif quantity * price != value:
                            code = 'position_value_mismatch'
                    elif row.symbol or quantity != 0 or price != 0:
                        code = 'invalid_cash_representation'
                    if code == 'ok':
                        totals[row.account_alias] = totals.get(row.account_alias, Decimal(0)) + value
                except ValueError:
                    code = 'invalid_decimal'
            outcomes.append(RowOutcome(index, 'accepted' if code == 'ok' else 'rejected', code))
    errors = []
    if any(item.status == 'rejected' for item in outcomes):
        errors.append('rejected_rows')
    if set(totals) != set(expected):
        errors.append('account_coverage_mismatch')
    if any(totals.get(alias) != value for alias, value in expected.items()):
        errors.append('account_total_mismatch')
    blocked = bool(errors)
    return Reconciliation('blocked' if blocked else 'reconciled', tuple(outcomes), tuple(errors),
                          () if blocked else tuple(rows),
                          () if blocked else tuple(sorted(totals.items())))


def parse_envelope(payload: dict, *, now=None, max_age=timedelta(days=4)) -> ImportEnvelope:
    """Parse a versioned normalized JSON envelope without broker assumptions."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload, dict) or now.tzinfo is None or max_age <= timedelta(0):
        raise ValueError('invalid_envelope')
    required = {'schema_version', 'mode', 'currency', 'source_type', 'source_id',
                'as_of', 'expected_totals', 'rows'}
    if set(payload) != required or payload.get('schema_version') != 1:
        raise ValueError('unsupported_schema')
    mode, source_type = payload.get('mode'), payload.get('source_type')
    expected_source = {'synthetic': 'normalized_synthetic',
                       'user_export': 'normalized_user_export'}.get(mode)
    if expected_source is None or source_type != expected_source:
        raise ValueError('invalid_mode_source')
    if payload.get('currency') != 'USD':
        raise ValueError('unsupported_currency')
    source_id = payload.get('source_id')
    if not isinstance(source_id, str) or not re.fullmatch(r'SRC_[A-Z0-9]{8,32}', source_id):
        raise ValueError('invalid_source_id')
    try:
        as_of = datetime.fromisoformat(payload['as_of'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('invalid_as_of') from None
    if as_of.tzinfo is None or as_of > now or now - as_of > max_age:
        raise ValueError('stale_or_invalid_as_of')
    raw_rows = payload.get('rows')
    if not isinstance(raw_rows, list):
        raise ValueError('invalid_rows')
    fields = {'account_alias', 'asset_type', 'symbol', 'quantity', 'price', 'market_value'}
    rows = []
    for raw in raw_rows:
        if not isinstance(raw, dict) or set(raw) != fields:
            rows.append(raw)  # reconcile() records the row as invalid without echoing it
        else:
            rows.append(ImportRow(**raw))
    if not isinstance(payload.get('expected_totals'), dict):
        raise ValueError('invalid_expected_totals')
    return ImportEnvelope(1, mode, 'USD', source_type, source_id, as_of,
                          payload['expected_totals'], tuple(rows))


def reconcile_envelope(payload: dict, *, now=None, max_age=timedelta(days=4)):
    envelope = parse_envelope(payload, now=now, max_age=max_age)
    result = reconcile(list(envelope.rows), envelope.expected_totals)
    return {
        'schema_version': envelope.schema_version,
        'mode': envelope.mode,
        'currency': envelope.currency,
        'source_type': envelope.source_type,
        'source_id': envelope.source_id,
        'as_of': envelope.as_of.isoformat(),
        'status': result.status,
        'outcomes': [{'row_number': item.row_number, 'status': item.status, 'code': item.code}
                     for item in result.outcomes],
        'errors': list(result.errors),
        'account_totals': {alias: str(value) for alias, value in result.account_totals},
        'publishable_row_count': len(result.rows),
        'readiness': ('normalized reconciliation only; not Fidelity-validated'
                      if result.status == 'reconciled' else 'blocked; do not use for analysis'),
    }
