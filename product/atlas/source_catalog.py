"""Dated public-source candidates awaiting rights and extraction review."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import re
from urllib.parse import urlsplit

from .reference import resolve_security
from .watchlist_registry import WatchlistRegistry


_EXPECTED_SYMBOLS = ('NVDA', 'MU', 'AVGO', 'QCOM', 'PLTR', 'SPCX', 'QBTS', 'RGTI')
_SOURCE_KEYS = frozenset({
    'document_id', 'symbol', 'instrument_id', 'source_kind', 'source_uri',
    'published_on', 'observed_at', 'rights_state', 'extraction_state',
})
_PRIMARY_HOSTS = frozenset({
    'nvidianews.nvidia.com', 'investors.micron.com', 'investors.broadcom.com',
    'investor.qualcomm.com', 'investors.palantir.com', 'ir.spacex.com',
    'ir.dwavequantum.com', 'investors.rigetti.com',
})


@dataclass(frozen=True)
class SourceCandidate:
    document_id: str
    symbol: str
    instrument_id: str
    source_kind: str
    source_uri: str
    published_on: date
    observed_at: datetime
    rights_state: str
    extraction_state: str


@dataclass(frozen=True)
class PublicSourceCatalog:
    as_of: datetime
    candidates: tuple[SourceCandidate, ...]

    def public_summary(self) -> dict:
        return {
            'schema_version': 1,
            'as_of': self.as_of.isoformat(),
            'candidate_count': len(self.candidates),
            'items': [
                {
                    'symbol': candidate.symbol,
                    'identity_status': 'resolved',
                    'source_status': 'catalogued_public_candidate',
                    'rights_status': candidate.rights_state,
                    'extraction_status': candidate.extraction_state,
                    'metric_status': 'unavailable',
                    'decision': 'blocked_pending_rights_and_extraction',
                }
                for candidate in self.candidates
            ],
            'readiness': ('source addresses only; no retrieved bytes, metric values, '
                          'license conclusion or investment recommendation'),
        }


def _exact(value, keys, code):
    if not isinstance(value, dict) or frozenset(value) != keys:
        raise ValueError(code)
    return value


def _datetime(value, code):
    if not isinstance(value, str):
        raise ValueError(code)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(code) from error
    if parsed.tzinfo is None:
        raise ValueError(code)
    return parsed


def _date(value, code):
    if not isinstance(value, str):
        raise ValueError(code)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(code) from error


def _primary_source_uri(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and parsed.hostname in _PRIMARY_HOSTS and
            parsed.username is None and parsed.password is None and
            parsed.fragment == '')


def load_public_source_catalog(raw: bytes, registry: WatchlistRegistry, *, now=None):
    """Validate source candidates without promoting them to usable evidence."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(raw, bytes) or not raw or len(raw) > 65_536:
        raise ValueError('invalid_source_catalog_size')
    if not isinstance(registry, WatchlistRegistry):
        raise ValueError('invalid_source_catalog_registry')
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_source_catalog_time')
    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_source_catalog') from error
    payload = _exact(payload, frozenset({'schema_version', 'as_of', 'sources'}),
                     'invalid_source_catalog_schema')
    as_of = _datetime(payload['as_of'], 'invalid_source_catalog_as_of')
    if (payload['schema_version'] != 1 or as_of > now or
            as_of != registry.as_of or not isinstance(payload['sources'], list)):
        raise ValueError('unsupported_source_catalog')

    candidates = []
    for item in payload['sources']:
        item = _exact(item, _SOURCE_KEYS, 'invalid_source_candidate_schema')
        published_on = _date(item['published_on'], 'invalid_source_published_on')
        observed_at = _datetime(item['observed_at'], 'invalid_source_observed_at')
        if (not re.fullmatch(r'DOC_[A-Z0-9]{12,32}', item['document_id']) or
                item['source_kind'] != 'issuer_release' or
                not _primary_source_uri(item['source_uri']) or
                published_on > as_of.date() or observed_at != as_of or
                item['rights_state'] != 'not_evaluated' or
                item['extraction_state'] != 'not_attempted'):
            raise ValueError('invalid_source_candidate')
        resolution = resolve_security(
            list(registry.records), symbol=item['symbol'], exchange_mic='XNAS',
            on_date=as_of.date(), now=now)
        if (resolution.status != 'resolved' or
                resolution.instrument_id != item['instrument_id']):
            raise ValueError('source_candidate_identity_mismatch')
        candidates.append(SourceCandidate(
            item['document_id'], item['symbol'], item['instrument_id'],
            item['source_kind'], item['source_uri'], published_on, observed_at,
            item['rights_state'], item['extraction_state']))

    symbols = [candidate.symbol for candidate in candidates]
    documents = [candidate.document_id for candidate in candidates]
    if (tuple(symbols) != _EXPECTED_SYMBOLS or len(documents) != len(set(documents))):
        raise ValueError('incomplete_source_catalog')
    return PublicSourceCatalog(as_of, tuple(candidates))
