"""Extraction-quality evidence bound to exact source and metric payload bytes."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Literal

from .metric_evidence import MetricPayload
from .source_evidence import ResearchSourceRecord


ExtractionMethod = Literal['deterministic_parser', 'manual_entry', 'llm_assisted']
ReviewStatus = Literal['not_required', 'unverified', 'verified', 'rejected']


def _matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


@dataclass(frozen=True)
class ExtractionEvidence:
    extraction_id: str
    document_id: str
    metric_id: str
    source_sha256: str
    payload_sha256: str
    method: ExtractionMethod
    extractor_version: str
    extracted_at: datetime
    review_status: ReviewStatus
    reviewer_evidence_sha256: str | None

    def __post_init__(self):
        fields = (
            (r'EXT_[A-Z0-9]{12,32}', self.extraction_id),
            (r'DOC_[A-Z0-9]{12,32}', self.document_id),
            (r'MET_[A-Z0-9_]{4,40}', self.metric_id),
            (r'[0-9a-f]{64}', self.source_sha256),
            (r'[0-9a-f]{64}', self.payload_sha256),
            (r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
             self.extractor_version),
        )
        if any(not _matches(pattern, value) for pattern, value in fields):
            raise ValueError('invalid_extraction_evidence')
        if self.method not in ('deterministic_parser', 'manual_entry', 'llm_assisted'):
            raise ValueError('invalid_extraction_method')
        if self.review_status not in ('not_required', 'unverified', 'verified', 'rejected'):
            raise ValueError('invalid_extraction_review_status')
        if not isinstance(self.extracted_at, datetime) or self.extracted_at.tzinfo is None:
            raise ValueError('invalid_extracted_at')
        has_review_hash = _matches(r'[0-9a-f]{64}', self.reviewer_evidence_sha256)
        if ((self.reviewer_evidence_sha256 is not None and not has_review_hash) or
                (self.review_status in ('verified', 'rejected')) != has_review_hash or
                (self.method != 'deterministic_parser' and
                 self.review_status == 'not_required')):
            raise ValueError('invalid_extraction_review_evidence')


@dataclass(frozen=True)
class ExtractionDecision:
    status: Literal['ready', 'blocked']
    codes: tuple[str, ...]
    extraction_id: str | None


def assess_extraction_quality(evidence, source, payload, *, now=None):
    """Release an extraction reference only when exact bindings and review pass."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(evidence, ExtractionEvidence) or
            not isinstance(source, ResearchSourceRecord) or
            not isinstance(payload, MetricPayload) or
            not isinstance(now, datetime) or now.tzinfo is None):
        raise ValueError('invalid_extraction_quality_request')
    codes = []
    if evidence.extracted_at < source.retrieved_at:
        codes.append('extraction_before_retrieval')
    if evidence.extracted_at > now:
        codes.append('extraction_in_future')
    checks = (
        ('extraction_document_mismatch', evidence.document_id, source.document_id),
        ('extraction_source_hash_mismatch', evidence.source_sha256,
         source.source_sha256),
        ('extraction_metric_mismatch', evidence.metric_id,
         payload.metric.definition.metric_id),
        ('extraction_payload_hash_mismatch', evidence.payload_sha256,
         payload.payload_sha256),
    )
    codes.extend(code for code, actual, expected in checks if actual != expected)
    if evidence.review_status == 'rejected':
        codes.append('extraction_rejected')
    elif evidence.review_status == 'unverified':
        codes.append('extraction_review_required')
    if codes:
        return ExtractionDecision('blocked', tuple(codes), None)
    code = ('deterministic_extraction_verified'
            if evidence.method == 'deterministic_parser'
            else 'human_review_verified')
    return ExtractionDecision('ready', (code,), evidence.extraction_id)
