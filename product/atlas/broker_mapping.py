"""Synthetic broker-shaped mapping harness; not a Fidelity adapter."""
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import io
import re

from .ingestion import reconcile_envelope


_CANONICAL_FIELDS = ('account_key', 'row_type', 'ticker', 'quantity', 'price',
                     'market_value')
_ASSET_TYPES = {'equity', 'cash', 'core_cash'}


@dataclass(frozen=True)
class MappingProfile:
    """Versioned description of a synthetic source layout and its semantics."""
    profile_id: str
    schema_version: int
    currency: str
    headers: tuple[tuple[str, str], ...]
    row_types: tuple[tuple[str, str], ...]
    rounding_policy: str
    account_total_type: str = 'ACCOUNT_TOTAL'


SYNTHETIC_BROKER_PROFILE = MappingProfile(
    profile_id='MAP_SYNTHETIC1',
    schema_version=1,
    currency='USD',
    headers=tuple((field, field) for field in _CANONICAL_FIELDS),
    row_types=(('EQUITY', 'equity'), ('CASH', 'cash'), ('CORE_CASH', 'core_cash')),
    rounding_policy='exact',
)


def _profile_maps(profile: MappingProfile):
    if (not isinstance(profile, MappingProfile) or
            not isinstance(profile.profile_id, str) or
            not re.fullmatch(r'MAP_[A-Z0-9]{8,32}', profile.profile_id) or
            profile.schema_version != 1 or profile.currency != 'USD' or
            profile.rounding_policy != 'exact' or
            not isinstance(profile.account_total_type, str) or
            re.fullmatch(r'[A-Z][A-Z0-9_]{0,31}', profile.account_total_type) is None or
            not isinstance(profile.headers, tuple) or
            not isinstance(profile.row_types, tuple) or not profile.row_types):
        raise ValueError('invalid_mapping_profile')
    try:
        headers, row_types = dict(profile.headers), dict(profile.row_types)
    except (TypeError, ValueError):
        raise ValueError('invalid_mapping_profile') from None
    source_headers = list(headers.values())
    if (len(headers) != len(profile.headers) or set(headers) != set(_CANONICAL_FIELDS) or
            any(not isinstance(name, str) or
                re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]{0,63}', name) is None
                for name in source_headers)):
        raise ValueError('invalid_mapping_profile')
    if (len(source_headers) != len(set(source_headers)) or
            len(row_types) != len(profile.row_types) or
            profile.account_total_type in row_types or
            any(not isinstance(source, str) or not isinstance(target, str) or
                re.fullmatch(r'[A-Z][A-Z0-9_]{0,31}', source) is None or
                target not in _ASSET_TYPES for source, target in row_types.items())):
        raise ValueError('invalid_mapping_profile')
    return headers, row_types


def map_synthetic_broker_export(payload: dict, *, profile=SYNTHETIC_BROKER_PROFILE,
                                now=None, max_age=timedelta(days=4)) -> dict:
    """Map an invented broker-shaped payload into Atlas's normalized envelope.

    Every source row produces one normalized or invalid placeholder row so
    downstream reconciliation cannot silently omit unsupported/malformed data.
    """
    now = now or datetime.now(timezone.utc)
    headers, row_types = _profile_maps(profile)
    required = {'schema_version', 'mode', 'currency', 'source_type', 'source_id',
                'as_of', 'expected_totals', 'rows'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError('unsupported_broker_mapping_schema')
    if (payload.get('schema_version') != 1 or payload.get('mode') != 'synthetic' or
            payload.get('currency') != profile.currency or
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
    source_fields = set(headers.values())
    for raw in raw_rows:
        account_field, type_field = headers['account_key'], headers['row_type']
        if (not isinstance(raw, dict) or set(raw) != source_fields or
                not isinstance(raw.get(account_field), str) or
                raw.get(account_field) not in aliases or
                not isinstance(raw.get(type_field), str)):
            mapped.append({'invalid_row': True})
            continue
        source_row_type = raw[type_field]
        asset_type = row_types.get(source_row_type, source_row_type.lower())
        ticker = raw[headers['ticker']]
        if asset_type in ('cash', 'core_cash'):
            ticker = ''
        mapped.append({
            'account_alias': aliases[raw[account_field]],
            'asset_type': asset_type,
            'symbol': ticker,
            'quantity': raw[headers['quantity']],
            'price': raw[headers['price']],
            'market_value': raw[headers['market_value']],
        })

    normalized = {
        'schema_version': 1,
        'mode': 'synthetic',
        'currency': profile.currency,
        'source_type': 'normalized_synthetic',
        'source_id': payload['source_id'],
        'as_of': payload['as_of'],
        'expected_totals': {aliases[key]: value for key, value in raw_totals.items()},
        'rows': mapped,
    }
    result = reconcile_envelope(normalized, now=now, max_age=max_age)
    result['mapping_contract'] = 'synthetic_broker_v1'
    result['mapping_profile'] = {
        'profile_id': profile.profile_id,
        'schema_version': profile.schema_version,
        'currency': profile.currency,
        'rounding_policy': profile.rounding_policy,
    }
    result['input_row_count'] = len(raw_rows)
    result['mapped_row_count'] = len(mapped)
    result['readiness'] = ('synthetic broker mapping reconciled; not Fidelity-validated'
                           if result['status'] == 'reconciled'
                           else 'blocked synthetic mapping; do not use for analysis')
    return result


def parse_synthetic_delimited(source_bytes: bytes, *, source_id: str, as_of: str,
                              profile=SYNTHETIC_BROKER_PROFILE, now=None,
                              max_age=timedelta(days=4)) -> dict:
    """Parse a bounded invented CSV layout and reconcile it through the profile.

    The first record must be the exact profile header. ACCOUNT_TOTAL footer
    records supply source-reported account totals and must follow all data rows.
    Malformed/data-after-footer records become invalid mapped rows rather than
    disappearing. This is deliberately not a Fidelity parser.
    """
    headers, _ = _profile_maps(profile)
    if not isinstance(source_bytes, bytes) or not source_bytes or len(source_bytes) > 1_000_000:
        raise ValueError('invalid_delimited_source')
    try:
        text = source_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('invalid_delimited_encoding') from None
    if '\x00' in text:
        raise ValueError('invalid_delimited_encoding')
    try:
        records = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except csv.Error:
        raise ValueError('invalid_delimited_syntax') from None
    expected_header = [headers[field] for field in _CANONICAL_FIELDS]
    if not records or records[0] != expected_header:
        raise ValueError('unexpected_delimited_header')
    if len(records) == 1 or len(records) - 1 > 10_000:
        raise ValueError('invalid_delimited_record_count')

    rows, totals = [], {}
    footer_started = False
    footer_count = 0
    for record in records[1:]:
        if len(record) != len(expected_header):
            rows.append({'invalid_delimited_row': True})
            continue
        raw = dict(zip(expected_header, record))
        if raw[headers['row_type']] == profile.account_total_type:
            footer_started = True
            footer_count += 1
            account_key = raw[headers['account_key']]
            if (not account_key or account_key in totals or raw[headers['ticker']] or
                    raw[headers['quantity']] or raw[headers['price']] or
                    not raw[headers['market_value']]):
                raise ValueError('invalid_account_total_footer')
            totals[account_key] = raw[headers['market_value']]
        elif footer_started:
            rows.append({'invalid_delimited_row': True})
        else:
            rows.append(raw)
    if not totals:
        raise ValueError('account_total_footer_required')
    if not rows:
        raise ValueError('position_rows_required')

    payload = {
        'schema_version': 1,
        'mode': 'synthetic',
        'currency': profile.currency,
        'source_type': 'broker_mapping_synthetic',
        'source_id': source_id,
        'as_of': as_of,
        'expected_totals': totals,
        'rows': rows,
    }
    result = map_synthetic_broker_export(
        payload, profile=profile, now=now, max_age=max_age)
    result['parser_contract'] = 'synthetic_delimited_v1'
    result['source_byte_count'] = len(source_bytes)
    result['header_record_count'] = 1
    result['position_record_count'] = len(rows)
    result['footer_record_count'] = footer_count
    result['delimited_record_count'] = len(records)
    return result
