"""Deterministic blank worksheet for private manual source-rights review."""
from dataclasses import dataclass

from .rights_evidence import REVIEW_CHECKLIST
from .source_catalog import PublicSourceCatalog
from .source_rights import SourceRightsManifest


EVIDENCE_SLOTS = (
    'review_id',
    'terms_uri',
    'evidence_sha256',
    'terms_observed_at',
    'reviewed_at',
    'valid_until',
    'reviewer_reference',
    'conclusion',
    'permitted_actions',
)
ALLOWED_CONCLUSIONS = ('permitted', 'prohibited', 'needs_counsel')
ALLOWED_ACTIONS = (
    'retrieve_once', 'extract_internal', 'retain_private', 'cite_excerpt',
)


@dataclass(frozen=True)
class RightsReviewWorksheetItem:
    document_id: str
    symbol: str
    source_uri: str
    review_state: str

    def template_summary(self):
        return {
            'document_id': self.document_id,
            'symbol': self.symbol,
            'source_uri': self.source_uri,
            'review_state': self.review_state,
            'next_action': 'complete_manual_terms_review_privately',
        }


@dataclass(frozen=True)
class RightsReviewWorksheet:
    use_case: str
    items: tuple[RightsReviewWorksheetItem, ...]

    def public_readiness_summary(self):
        """Return count-only readiness without source or review evidence fields."""
        review_task_count = len(self.items)
        required_check_count = review_task_count * len(REVIEW_CHECKLIST)
        return {
            'schema_version': 1,
            'status': 'blocked',
            'review_task_count': review_task_count,
            'pending_review_count': review_task_count,
            'required_check_count': required_check_count,
            'completed_check_count': 0,
            'pending_check_count': required_check_count,
            'evidence_storage': 'private_outside_repository',
            'technical_retrieval_status': 'disabled_separate_gate',
            'release_authorized': False,
            'next_action': 'complete_manual_terms_review_privately',
        }

    def template_summary(self):
        return {
            'schema_version': 1,
            'status': 'blocked',
            'template_only': True,
            'use_case': self.use_case,
            'candidate_count': len(self.items),
            'evidence_storage': 'private_outside_repository',
            'evidence_slots': list(EVIDENCE_SLOTS),
            'allowed_conclusions': list(ALLOWED_CONCLUSIONS),
            'allowed_actions': list(ALLOWED_ACTIONS),
            'checklist': [
                {'item': item, 'status': 'pending'}
                for item in REVIEW_CHECKLIST
            ],
            'items': [item.template_summary() for item in self.items],
            'technical_retrieval_status': 'disabled_separate_gate',
            'release_authorized': False,
            'readiness': ('blank worksheet only; no terms evidence, reviewer, '
                          'permission conclusion, retrieval or release authority'),
        }


def build_rights_review_worksheet(catalog, manifest):
    """Bind blank review tasks to the exact source catalog without deciding rights."""
    if (not isinstance(catalog, PublicSourceCatalog) or
            not isinstance(manifest, SourceRightsManifest) or
            manifest.use_case != 'internal_research' or
            manifest.assessed_at < catalog.as_of or
            manifest.policy.follow_redirects or
            manifest.policy.retain_source_bytes or
            manifest.policy.network_fetch_enabled):
        raise ValueError('invalid_rights_review_worksheet_input')

    candidates = [(item.document_id, item.symbol) for item in catalog.candidates]
    reviews = [(item.document_id, item.symbol) for item in manifest.reviews]
    if (reviews != candidates or
            any(item.review_state != 'not_started' for item in manifest.reviews)):
        raise ValueError('rights_review_worksheet_catalog_mismatch')

    items = tuple(
        RightsReviewWorksheetItem(
            candidate.document_id, candidate.symbol, candidate.source_uri,
            review.review_state)
        for candidate, review in zip(catalog.candidates, manifest.reviews)
    )
    return RightsReviewWorksheet(manifest.use_case, items)
