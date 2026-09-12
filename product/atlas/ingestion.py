"""Synthetic normalized import contract; NOT a Fidelity CSV adapter.

Fail-closed reconciliation: any rejected row or unmatched account total
prevents publication of accepted positions. No persistence or broker access.
"""
from collections import Counter
from dataclasses import dataclass
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
