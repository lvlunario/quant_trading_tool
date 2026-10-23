"""Two-key authorization receipt for bounded research-source capture.

This module does not fetch URLs, retain source bytes, extract metrics or grant
release authority. It combines an assessed rights decision with a separate,
exact-document technical approval and emits a redacted receipt.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import re

from .rights_evidence import RightsEvidenceReport
from .source_catalog import PublicSourceCatalog


MAX_CAPTURE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({
    'text/html', 'application/pdf', 'application/json',
})


@dataclass(frozen=True)
class TechnicalCaptureApproval:
    authorization_id: str
    document_id: str
    symbol: str
    use_case: str
    action: str
    approved_at: datetime
    valid_until: datetime
    max_source_bytes: int
    allowed_content_types: tuple[str, ...]
    follow_redirects: bool
    retain_source_bytes: bool

    def __post_init__(self):
        if (not isinstance(self.authorization_id, str) or
                re.fullmatch(r'AUTH_[A-Z0-9]{12,32}', self.authorization_id) is None or
                not isinstance(self.document_id, str) or
                re.fullmatch(r'DOC_[A-Z0-9]{12,32}', self.document_id) is None or
                not isinstance(self.symbol, str) or
                re.fullmatch(r'[A-Z][A-Z0-9.-]{0,15}', self.symbol) is None or
                self.use_case != 'internal_research' or
                self.action != 'retrieve_once' or
                not isinstance(self.approved_at, datetime) or
                self.approved_at.tzinfo is None or
                not isinstance(self.valid_until, datetime) or
                self.valid_until.tzinfo is None or
                self.approved_at >= self.valid_until or
                not isinstance(self.max_source_bytes, int) or
                isinstance(self.max_source_bytes, bool) or
                not 0 < self.max_source_bytes <= MAX_CAPTURE_BYTES or
                not isinstance(self.allowed_content_types, tuple) or
                not self.allowed_content_types or
                len(self.allowed_content_types) != len(set(self.allowed_content_types)) or
                set(self.allowed_content_types) - ALLOWED_CONTENT_TYPES or
                self.follow_redirects is not False or
                self.retain_source_bytes is not False):
            raise ValueError('invalid_technical_capture_approval')


@dataclass(frozen=True)
class SourceCaptureAuthorizationItem:
    symbol: str
    rights_allowed: bool
    capture_authorized: bool
    decision: str


@dataclass(frozen=True)
class SourceCaptureAuthorizationReceipt:
    assessed_at: datetime
    items: tuple[SourceCaptureAuthorizationItem, ...]

    def public_summary(self) -> dict:
        rights_ready = sum(item.rights_allowed for item in self.items)
        authorized = sum(item.capture_authorized for item in self.items)
        return {
            'schema_version': 1,
            'status': 'ready' if authorized == len(self.items) else 'blocked',
            'assessed_at': self.assessed_at.isoformat(),
            'candidate_count': len(self.items),
            'rights_ready_count': rights_ready,
            'capture_authorized_count': authorized,
            'items': [
                {
                    'symbol': item.symbol,
                    'rights_allowed': item.rights_allowed,
                    'capture_authorized': item.capture_authorized,
                    'decision': item.decision,
                }
                for item in self.items
            ],
            'source_bytes_status': 'not_provided',
            'release_authorized': False,
            'readiness': ('two-key authorization receipt only; no network fetch, '
                          'retained bytes, extraction, metric or release authority'),
        }


def assess_source_capture_authorization(catalog, rights, approvals=(), *, at=None):
    """Require reviewed rights and a separate current technical approval."""
    at = at or datetime.now(timezone.utc)
    if (not isinstance(catalog, PublicSourceCatalog) or
            not isinstance(rights, RightsEvidenceReport) or
            not isinstance(approvals, (tuple, list)) or
            any(not isinstance(item, TechnicalCaptureApproval)
                for item in approvals) or
            not isinstance(at, datetime) or at.tzinfo is None or
            rights.assessed_at != at or rights.assessed_at < catalog.as_of or
            [item.symbol for item in rights.items] !=
            [item.symbol for item in catalog.candidates]):
        raise ValueError('invalid_source_capture_authorization_input')

    authorization_ids = [item.authorization_id for item in approvals]
    document_ids = [item.document_id for item in approvals]
    if (len(authorization_ids) != len(set(authorization_ids)) or
            len(document_ids) != len(set(document_ids))):
        raise ValueError('duplicate_technical_capture_approval')

    candidates = {(item.document_id, item.symbol) for item in catalog.candidates}
    if any((item.document_id, item.symbol) not in candidates for item in approvals):
        raise ValueError('technical_capture_catalog_mismatch')

    results = []
    for candidate, rights_item in zip(catalog.candidates, rights.items):
        if not rights_item.rights_allowed:
            results.append(SourceCaptureAuthorizationItem(
                candidate.symbol, False, False, rights_item.code))
            continue
        matches = [item for item in approvals
                   if item.document_id == candidate.document_id and
                   item.symbol == candidate.symbol]
        if not matches:
            results.append(SourceCaptureAuthorizationItem(
                candidate.symbol, True, False, 'technical_approval_missing'))
            continue
        approval = matches[0]
        if at < approval.approved_at:
            decision = 'technical_approval_not_yet_effective'
            authorized = False
        elif at >= approval.valid_until:
            decision = 'technical_approval_expired'
            authorized = False
        else:
            decision = 'source_capture_authorized'
            authorized = True
        results.append(SourceCaptureAuthorizationItem(
            candidate.symbol, True, authorized, decision))
    return SourceCaptureAuthorizationReceipt(at, tuple(results))
