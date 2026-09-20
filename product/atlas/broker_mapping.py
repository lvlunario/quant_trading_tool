"""Synthetic broker-shaped mapping harness; not a Fidelity adapter."""
from datetime import datetime, timedelta, timezone
import re

from .ingestion import reconcile_envelope


_FIELDS = {'account_key', 'row_type', 'ticker', 'quantity', 'price', 'market_value'}
_ROW_TYPES = {'EQUITY': 'equity', 'CASH': 'cash', 'CORE_CASH': 'core_cash'}


def map_synthetic_broker_export(payload: dict, *, now=None,
                                max_age=timedelta(days=4)) -> dict:
    """Map an invented broker-shaped payload into Atlas's normalized envelope.

    Every source row produces one normalized or invalid placeholder row so
    downstream reconciliation cannot silently omit unsupported/malformed data.
    """
    now = now or datetime.now(timezone.utc)
    required = {'schema_version', 'mode', 'currency', 'source_type', 'source_id',
                'as_of', 'expected_totals', 'rows'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError('unsupported_broker_mapping_schema')
    if (payload.get('schema_version') != 1 or payload.get('mode') != 'synthetic' or
            payload.get('currency') != 'USD' or
            payload.get('source_type') != 'broker_mapping_synthetic'):
        raise ValueError('unsupported_broker_mapping_contract')
    raw_rows, raw_totals = payload.get('rows'), payload.get('expected_totals')
    if not isinstance(raw_rows, list) or not raw_rows or len(raw_rows) > 10000:
        raise ValueError('invalid_broker_row_count')
    if not isinstance(raw_totals, dict) or not raw_totals:
        raise ValueError('broker_expected_totals_required')

    alias_pattern = r'[A-Z]{1,16}'
    aliases = {}
    for key in raw_totals:
        if not isinstance(key, str) or re.fullmatch(alias_pattern, key) is None:
            raise ValueError('invalid_broker_account_key')
        aliases[key] = f'ACCT_{key}'

    mapped = []
    for raw in raw_rows:
        if (not isinstance(raw, dict) or set(raw) != _FIELDS or
                not isinstance(raw.get('account_key'), str) or
                raw.get('account_key') not in aliases or
                not isinstance(raw.get('row_type'), str)):
            mapped.append({'invalid_row': True})
            continue
        asset_type = _ROW_TYPES.get(raw['row_type'], raw['row_type'].lower())
        ticker = raw['ticker']
        if raw['row_type'] in ('CASH', 'CORE_CASH'):
            ticker = ''
        mapped.append({
            'account_alias': aliases[raw['account_key']],
            'asset_type': asset_type,
            'symbol': ticker,
            'quantity': raw['quantity'],
            'price': raw['price'],
            'market_value': raw['market_value'],
        })

    normalized = {
        'schema_version': 1,
        'mode': 'synthetic',
        'currency': 'USD',
        'source_type': 'normalized_synthetic',
        'source_id': payload['source_id'],
        'as_of': payload['as_of'],
        'expected_totals': {aliases[key]: value for key, value in raw_totals.items()},
        'rows': mapped,
    }
    result = reconcile_envelope(normalized, now=now, max_age=max_age)
    result['mapping_contract'] = 'synthetic_broker_v1'
    result['input_row_count'] = len(raw_rows)
    result['mapped_row_count'] = len(mapped)
    result['readiness'] = ('synthetic broker mapping reconciled; not Fidelity-validated'
                           if result['status'] == 'reconciled'
                           else 'blocked synthetic mapping; do not use for analysis')
    return result
