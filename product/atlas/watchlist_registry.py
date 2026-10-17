"""Bounded public watchlist identity registry for the M2 research workbench."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from urllib.parse import urlsplit

from .reference import SecurityRecord, resolve_security


_EXPECTED_SYMBOLS = frozenset(
    {'NVDA', 'MU', 'QCOM', 'PLTR', 'SPCX', 'CRBS', 'QBTS', 'RGTI', 'AVGO'})
_RECORD_KEYS = frozenset({
    'instrument_id', 'issuer_id', 'issuer_name', 'security_name',
    'exchange_mic', 'currency', 'security_class', 'symbol', 'effective_from',
    'effective_to', 'source_uri', 'observed_at',
})
_BLOCKED_KEYS = frozenset({'symbol', 'code', 'checked_at', 'checked_sources'})
_PRIMARY_HOSTS = frozenset({'www.nasdaq.com', 'www.sec.gov'})


@dataclass(frozen=True)
class WatchlistRegistry:
    as_of: datetime
    records: tuple[SecurityRecord, ...]
    blocked: tuple[dict, ...]

    def public_summary(self) -> dict:
        return {
            'schema_version': 1,
            'as_of': self.as_of.isoformat(),
            'resolved_count': len(self.records),
            'blocked_count': len(self.blocked),
            'resolved_symbols': [record.symbol for record in self.records],
            'blocked': [
                {'symbol': item['symbol'], 'code': item['code']}
                for item in self.blocked
            ],
            'readiness': ('current public identity metadata only; no prices, '
                          'holdings, provider license or investment conclusion'),
        }


def _exact(value: dict, keys: frozenset, code: str) -> dict:
    if not isinstance(value, dict) or frozenset(value) != keys:
        raise ValueError(code)
    return value


def _datetime(value, code: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(code)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(code) from error
    if parsed.tzinfo is None:
        raise ValueError(code)
    return parsed


def _date(value, code: str) -> date:
    if not isinstance(value, str):
        raise ValueError(code)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(code) from error


def _primary_uri(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and parsed.hostname in _PRIMARY_HOSTS and
            parsed.username is None and parsed.password is None and
            parsed.fragment == '')


def load_public_watchlist_registry(raw: bytes, *, now=None) -> WatchlistRegistry:
    """Load an exact public registry; unknown, overlapping or future data fails."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(raw, bytes) or not raw or len(raw) > 65_536:
        raise ValueError('invalid_watchlist_registry_size')
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_watchlist_registry_time')
    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_watchlist_registry') from error
    payload = _exact(payload, frozenset({'schema_version', 'as_of', 'records', 'blocked'}),
                     'invalid_watchlist_registry_schema')
    as_of = _datetime(payload['as_of'], 'invalid_watchlist_as_of')
    if payload['schema_version'] != 1 or as_of > now:
        raise ValueError('unsupported_watchlist_registry')
    if (not isinstance(payload['records'], list) or
            not isinstance(payload['blocked'], list)):
        raise ValueError('invalid_watchlist_entries')

    records = []
    for entry in payload['records']:
        entry = _exact(entry, _RECORD_KEYS, 'invalid_watchlist_record_schema')
        if not _primary_uri(entry['source_uri']):
            raise ValueError('unapproved_identity_source')
        observed_at = _datetime(entry['observed_at'], 'invalid_watchlist_observed_at')
        effective_to = (None if entry['effective_to'] is None else
                        _date(entry['effective_to'], 'invalid_watchlist_effective_to'))
        record = SecurityRecord(
            instrument_id=entry['instrument_id'], issuer_id=entry['issuer_id'],
            issuer_name=entry['issuer_name'], security_name=entry['security_name'],
            exchange_mic=entry['exchange_mic'], currency=entry['currency'],
            security_class=entry['security_class'], symbol=entry['symbol'],
            effective_from=_date(entry['effective_from'],
                                 'invalid_watchlist_effective_from'),
            effective_to=effective_to, source_uri=entry['source_uri'],
            observed_at=observed_at)
        if record.observed_at != as_of or record.exchange_mic != 'XNAS':
            raise ValueError('inconsistent_watchlist_record')
        records.append(record)

    blocked = []
    for entry in payload['blocked']:
        entry = _exact(entry, _BLOCKED_KEYS, 'invalid_blocked_identity_schema')
        checked_at = _datetime(entry['checked_at'], 'invalid_blocked_identity_time')
        sources = entry['checked_sources']
        if (entry['code'] != 'unresolved_no_authoritative_match' or
                checked_at != as_of or not isinstance(sources, list) or
                not sources or any(not _primary_uri(uri) for uri in sources)):
            raise ValueError('invalid_blocked_identity')
        blocked.append({**entry, 'checked_at': checked_at,
                        'checked_sources': tuple(sources)})

    symbols = [record.symbol for record in records] + [item['symbol'] for item in blocked]
    if (set(symbols) != _EXPECTED_SYMBOLS or len(symbols) != len(set(symbols)) or
            {item['symbol'] for item in blocked} != {'CRBS'}):
        raise ValueError('incomplete_watchlist_universe')
    for record in records:
        decision = resolve_security(records, symbol=record.symbol,
                                    exchange_mic=record.exchange_mic,
                                    on_date=as_of.date(), now=now)
        if decision.status != 'resolved' or decision.instrument_id != record.instrument_id:
            raise ValueError('unresolved_watchlist_record')
    return WatchlistRegistry(as_of, tuple(records), tuple(blocked))

