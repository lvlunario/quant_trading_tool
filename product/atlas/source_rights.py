"""Document-level rights review and bounded retrieval planning."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json

from .source_catalog import PublicSourceCatalog


_REVIEW_KEYS = frozenset({
    'document_id', 'symbol', 'review_state', 'terms_uri',
    'evidence_sha256', 'reviewed_at', 'valid_until',
})
_POLICY_KEYS = frozenset({
    'max_source_bytes', 'allowed_content_types', 'follow_redirects',
    'retain_source_bytes', 'network_fetch_enabled',
})
_SAFE_POLICY = {
    'max_source_bytes': 5 * 1024 * 1024,
    'allowed_content_types': ['text/html', 'application/pdf', 'application/json'],
    'follow_redirects': False,
    'retain_source_bytes': False,
    'network_fetch_enabled': False,
}


@dataclass(frozen=True)
class SourceRightsReview:
    document_id: str
    symbol: str
    review_state: str


@dataclass(frozen=True)
class RetrievalPolicy:
    max_source_bytes: int
    allowed_content_types: tuple[str, ...]
    follow_redirects: bool
    retain_source_bytes: bool
    network_fetch_enabled: bool


@dataclass(frozen=True)
class SourceRightsManifest:
    assessed_at: datetime
    use_case: str
    policy: RetrievalPolicy
    reviews: tuple[SourceRightsReview, ...]

    def public_summary(self) -> dict:
        return {
            'schema_version': 1,
            'status': 'blocked',
            'assessed_at': self.assessed_at.isoformat(),
            'use_case': self.use_case,
            'review_count': len(self.reviews),
            'items': [
                {
                    'symbol': review.symbol,
                    'rights_status': review.review_state,
                    'retrieval_status': 'blocked',
                    'decision': 'terms_evidence_required',
                }
                for review in self.reviews
            ],
            'retrieval_policy': {
                'max_source_bytes': self.policy.max_source_bytes,
                'allowed_content_types': list(self.policy.allowed_content_types),
                'follow_redirects': self.policy.follow_redirects,
                'retain_source_bytes': self.policy.retain_source_bytes,
                'network_fetch_enabled': self.policy.network_fetch_enabled,
            },
            'readiness': ('review tracking only; no terms evidence, retrieved bytes, '
                          'permission conclusion, metric or recommendation'),
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


def load_source_rights_manifest(raw: bytes, catalog: PublicSourceCatalog, *, now=None):
    """Load an explicitly unreviewed manifest without authorizing retrieval."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(raw, bytes) or not raw or len(raw) > 65_536:
        raise ValueError('invalid_source_rights_size')
    if not isinstance(catalog, PublicSourceCatalog):
        raise ValueError('invalid_source_rights_catalog')
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_source_rights_time')
    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_source_rights_manifest') from error
    payload = _exact(
        payload,
        frozenset({'schema_version', 'assessed_at', 'use_case',
                   'retrieval_policy', 'reviews'}),
        'invalid_source_rights_schema')
    assessed_at = _datetime(payload['assessed_at'], 'invalid_source_rights_assessed_at')
    if (payload['schema_version'] != 1 or
            payload['use_case'] != 'internal_research' or
            assessed_at < catalog.as_of or assessed_at > now or
            not isinstance(payload['reviews'], list)):
        raise ValueError('unsupported_source_rights_manifest')

    policy = _exact(payload['retrieval_policy'], _POLICY_KEYS,
                    'invalid_retrieval_policy_schema')
    if policy != _SAFE_POLICY:
        raise ValueError('unsafe_retrieval_policy')

    reviews = []
    for item in payload['reviews']:
        item = _exact(item, _REVIEW_KEYS, 'invalid_source_rights_review_schema')
        if (item['review_state'] != 'not_started' or
                any(item[field] is not None for field in
                    ('terms_uri', 'evidence_sha256', 'reviewed_at', 'valid_until'))):
            raise ValueError('unsubstantiated_source_rights_review')
        reviews.append(SourceRightsReview(
            item['document_id'], item['symbol'], item['review_state']))

    expected = [(candidate.document_id, candidate.symbol)
                for candidate in catalog.candidates]
    actual = [(review.document_id, review.symbol) for review in reviews]
    if actual != expected:
        raise ValueError('source_rights_catalog_mismatch')

    retrieval_policy = RetrievalPolicy(
        policy['max_source_bytes'], tuple(policy['allowed_content_types']),
        policy['follow_redirects'], policy['retain_source_bytes'],
        policy['network_fetch_enabled'])
    return SourceRightsManifest(
        assessed_at, payload['use_case'], retrieval_policy, tuple(reviews))
