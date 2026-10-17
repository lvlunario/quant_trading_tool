"""Reviewed source-terms evidence without network or release authority."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from urllib.parse import urlsplit

from .source_catalog import PublicSourceCatalog


REVIEW_CHECKLIST = (
    'source_owner_identified',
    'terms_version_captured',
    'intended_use_evaluated',
    'automated_access_evaluated',
    'retention_evaluated',
    'display_evaluated',
    'redistribution_evaluated',
    'expiry_or_review_date_set',
)
_ACTIONS = frozenset({
    'retrieve_once', 'extract_internal', 'retain_private', 'cite_excerpt',
})
_RECORD_KEYS = frozenset({
    'review_id', 'document_id', 'symbol', 'use_case', 'conclusion',
    'permitted_actions', 'terms_uri', 'evidence_sha256', 'terms_observed_at',
    'reviewed_at', 'valid_until', 'reviewer_reference', 'checklist_completed',
})


def _identifier(pattern, value, code):
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError(code)


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


def _https_uri(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and
            parsed.fragment == '')


@dataclass(frozen=True)
class ReviewedRightsEvidence:
    review_id: str
    document_id: str
    symbol: str
    use_case: str
    conclusion: str
    permitted_actions: tuple[str, ...]
    terms_uri: str
    evidence_sha256: str
    terms_observed_at: datetime
    reviewed_at: datetime
    valid_until: datetime
    reviewer_reference: str
    checklist_completed: tuple[str, ...]

    def __post_init__(self):
        _identifier(r'REV_[A-Z0-9]{12,32}', self.review_id, 'invalid_review_id')
        _identifier(r'DOC_[A-Z0-9]{12,32}', self.document_id, 'invalid_document_id')
        _identifier(r'RVW_[A-Z0-9]{12,32}', self.reviewer_reference,
                    'invalid_reviewer_reference')
        if (not isinstance(self.symbol, str) or
                re.fullmatch(r'[A-Z][A-Z0-9.-]{0,15}', self.symbol) is None or
                self.use_case != 'internal_research' or
                self.conclusion not in ('permitted', 'prohibited', 'needs_counsel') or
                not isinstance(self.permitted_actions, tuple) or
                len(self.permitted_actions) != len(set(self.permitted_actions)) or
                set(self.permitted_actions) - _ACTIONS or
                (self.conclusion == 'permitted') != bool(self.permitted_actions) or
                not _https_uri(self.terms_uri) or
                not isinstance(self.evidence_sha256, str) or
                re.fullmatch(r'[0-9a-f]{64}', self.evidence_sha256) is None or
                self.checklist_completed != REVIEW_CHECKLIST or
                any(not isinstance(value, datetime) or value.tzinfo is None
                    for value in (self.terms_observed_at, self.reviewed_at,
                                  self.valid_until)) or
                not self.terms_observed_at <= self.reviewed_at < self.valid_until):
            raise ValueError('invalid_reviewed_rights_evidence')


@dataclass(frozen=True)
class RightsEvidenceItem:
    symbol: str
    rights_allowed: bool
    code: str


@dataclass(frozen=True)
class RightsEvidenceReport:
    assessed_at: datetime
    items: tuple[RightsEvidenceItem, ...]

    def public_summary(self) -> dict:
        allowed = sum(item.rights_allowed for item in self.items)
        return {
            'schema_version': 1,
            'status': 'ready' if allowed == len(self.items) else 'blocked',
            'assessed_at': self.assessed_at.isoformat(),
            'review_count': len(self.items),
            'rights_allowed_count': allowed,
            'items': [
                {
                    'symbol': item.symbol,
                    'rights_allowed': item.rights_allowed,
                    'decision': item.code,
                }
                for item in self.items
            ],
            'technical_retrieval_status': 'disabled_separate_gate',
            'release_authorized': False,
            'readiness': ('terms-review decision only; no retrieval, source bytes, '
                          'metric, recommendation or release authority'),
        }


def _parse_record(item, now):
    if not isinstance(item, dict) or frozenset(item) != _RECORD_KEYS:
        raise ValueError('invalid_reviewed_rights_schema')
    _identifier(r'REV_[A-Z0-9]{12,32}', item['review_id'], 'invalid_review_id')
    _identifier(r'DOC_[A-Z0-9]{12,32}', item['document_id'], 'invalid_document_id')
    _identifier(r'RVW_[A-Z0-9]{12,32}', item['reviewer_reference'],
                'invalid_reviewer_reference')
    if (not isinstance(item['symbol'], str) or
            re.fullmatch(r'[A-Z][A-Z0-9.-]{0,15}', item['symbol']) is None or
            item['use_case'] != 'internal_research' or
            item['conclusion'] not in ('permitted', 'prohibited', 'needs_counsel') or
            not isinstance(item['permitted_actions'], list) or
            len(item['permitted_actions']) != len(set(item['permitted_actions'])) or
            set(item['permitted_actions']) - _ACTIONS or
            (item['conclusion'] == 'permitted') != bool(item['permitted_actions']) or
            not _https_uri(item['terms_uri']) or
            not isinstance(item['evidence_sha256'], str) or
            re.fullmatch(r'[0-9a-f]{64}', item['evidence_sha256']) is None or
            item['checklist_completed'] != list(REVIEW_CHECKLIST)):
        raise ValueError('invalid_reviewed_rights_evidence')
    terms_observed_at = _datetime(
        item['terms_observed_at'], 'invalid_terms_observed_at')
    reviewed_at = _datetime(item['reviewed_at'], 'invalid_rights_reviewed_at')
    valid_until = _datetime(item['valid_until'], 'invalid_rights_valid_until')
    if not terms_observed_at <= reviewed_at <= now or valid_until <= reviewed_at:
        raise ValueError('invalid_reviewed_rights_timing')
    return ReviewedRightsEvidence(
        item['review_id'], item['document_id'], item['symbol'], item['use_case'],
        item['conclusion'], tuple(item['permitted_actions']), item['terms_uri'],
        item['evidence_sha256'], terms_observed_at, reviewed_at, valid_until,
        item['reviewer_reference'], tuple(item['checklist_completed']))


def load_reviewed_rights_evidence(raw: bytes, catalog: PublicSourceCatalog, *, now=None):
    """Load reviewed terms evidence; empty evidence remains a valid blocked input."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(raw, bytes) or not raw or len(raw) > 262_144:
        raise ValueError('invalid_reviewed_rights_size')
    if not isinstance(catalog, PublicSourceCatalog):
        raise ValueError('invalid_reviewed_rights_catalog')
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_reviewed_rights_time')
    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_reviewed_rights_manifest') from error
    if (not isinstance(payload, dict) or
            frozenset(payload) != frozenset({'schema_version', 'records'}) or
            payload['schema_version'] != 1 or not isinstance(payload['records'], list)):
        raise ValueError('invalid_reviewed_rights_manifest_schema')
    records = tuple(_parse_record(item, now) for item in payload['records'])
    review_ids = [record.review_id for record in records]
    if len(review_ids) != len(set(review_ids)):
        raise ValueError('duplicate_rights_review_id')
    candidates = {(item.document_id, item.symbol) for item in catalog.candidates}
    if any((record.document_id, record.symbol) not in candidates for record in records):
        raise ValueError('reviewed_rights_catalog_mismatch')
    return records


def assess_reviewed_rights(catalog: PublicSourceCatalog, records, *, at=None):
    """Assess latest document reviews without enabling technical retrieval."""
    at = at or datetime.now(timezone.utc)
    if (not isinstance(catalog, PublicSourceCatalog) or
            not isinstance(records, (tuple, list)) or
            any(not isinstance(record, ReviewedRightsEvidence) for record in records) or
            not isinstance(at, datetime) or at.tzinfo is None):
        raise ValueError('invalid_rights_evidence_assessment')
    results = []
    for candidate in catalog.candidates:
        matching = [record for record in records
                    if record.document_id == candidate.document_id and
                    record.symbol == candidate.symbol and record.reviewed_at <= at]
        if not matching:
            results.append(RightsEvidenceItem(
                candidate.symbol, False, 'missing_review_evidence'))
            continue
        latest_at = max(record.reviewed_at for record in matching)
        latest = [record for record in matching if record.reviewed_at == latest_at]
        signatures = {
            (record.conclusion, record.permitted_actions, record.evidence_sha256,
             record.valid_until) for record in latest
        }
        if len(signatures) != 1:
            results.append(RightsEvidenceItem(
                candidate.symbol, False, 'ambiguous_review_evidence'))
            continue
        record = latest[0]
        if at >= record.valid_until:
            decision = RightsEvidenceItem(candidate.symbol, False, 'expired_review_evidence')
        elif record.conclusion == 'prohibited':
            decision = RightsEvidenceItem(candidate.symbol, False, 'use_prohibited')
        elif record.conclusion == 'needs_counsel':
            decision = RightsEvidenceItem(candidate.symbol, False, 'counsel_review_required')
        elif not {'retrieve_once', 'extract_internal'}.issubset(record.permitted_actions):
            decision = RightsEvidenceItem(candidate.symbol, False, 'required_action_not_permitted')
        else:
            decision = RightsEvidenceItem(candidate.symbol, True, 'explicitly_permitted')
        results.append(decision)
    return RightsEvidenceReport(at, tuple(results))
