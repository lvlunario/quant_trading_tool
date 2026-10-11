"""Fail-closed technical qualification for a real research-data extractor."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Literal


EvidenceScope = Literal['synthetic', 'private_authorized']


def _matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _optional_identifier(pattern, value):
    return value is None or _matches(pattern, value)


@dataclass(frozen=True)
class ProviderQualificationPolicy:
    policy_id: str
    policy_version: str
    provider_id: str
    dataset_id: str
    extractor_version: str
    minimum_document_count: int = 30
    minimum_field_check_count: int = 200
    minimum_exact_match_rate: Decimal = Decimal('0.99')
    minimum_format_coverage_rate: Decimal = Decimal('1')
    maximum_critical_error_count: int = 0
    maximum_semantic_mismatch_count: int = 0
    minimum_independent_reviewer_count: int = 2

    def __post_init__(self):
        identifiers = (
            (r'QPOL_[A-Z0-9]{12,32}', self.policy_id),
            (r'\d{1,6}\.\d{1,6}\.\d{1,6}', self.policy_version),
            (r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            (r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
            (r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
             self.extractor_version),
        )
        counts = (self.minimum_document_count, self.minimum_field_check_count,
                  self.maximum_critical_error_count,
                  self.maximum_semantic_mismatch_count,
                  self.minimum_independent_reviewer_count)
        if (any(not _matches(pattern, value) for pattern, value in identifiers) or
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in counts) or
                self.minimum_document_count < 1 or
                self.minimum_field_check_count < 1 or
                self.minimum_independent_reviewer_count < 2 or
                not isinstance(self.minimum_exact_match_rate, Decimal) or
                not Decimal('0') < self.minimum_exact_match_rate <= Decimal('1') or
                not isinstance(self.minimum_format_coverage_rate, Decimal) or
                not Decimal('0') < self.minimum_format_coverage_rate <= Decimal('1')):
            raise ValueError('invalid_provider_qualification_policy')


@dataclass(frozen=True)
class ProviderQualificationEvidence:
    evidence_id: str
    scope: EvidenceScope
    provider_id: str
    dataset_id: str
    extractor_version: str
    private_boundary_receipt_id: str | None
    authorization_receipt_id: str | None
    corpus_digest: str | None
    label_set_digest: str | None
    reviewer_ids: tuple[str, ...]
    supported_formats: tuple[str, ...]
    tested_formats: tuple[str, ...]
    document_count: int
    field_check_count: int
    exact_match_count: int
    critical_error_count: int
    semantic_mismatch_count: int
    evaluated_at: datetime
    expires_at: datetime

    def __post_init__(self):
        identifiers = (
            (r'QEV_[A-Z0-9]{12,32}', self.evidence_id),
            (r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            (r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
            (r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
             self.extractor_version),
        )
        counts = (self.document_count, self.field_check_count,
                  self.exact_match_count, self.critical_error_count,
                  self.semantic_mismatch_count)
        sequences = (self.reviewer_ids, self.supported_formats, self.tested_formats)
        if (self.scope not in ('synthetic', 'private_authorized') or
                any(not _matches(pattern, value) for pattern, value in identifiers) or
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in counts) or
                self.exact_match_count > self.field_check_count or
                any(not isinstance(value, tuple) for value in sequences) or
                any(not _matches(r'REV_[A-Z0-9]{8,24}', value)
                    for value in self.reviewer_ids) or
                any(not _matches(r'[a-z0-9][a-z0-9_.-]{0,39}', value)
                    for values in (self.supported_formats, self.tested_formats)
                    for value in values) or
                any(len(set(values)) != len(values) for values in sequences) or
                not isinstance(self.evaluated_at, datetime) or
                self.evaluated_at.tzinfo is None or
                not isinstance(self.expires_at, datetime) or
                self.expires_at.tzinfo is None or
                self.expires_at <= self.evaluated_at or
                not _optional_identifier(r'BOUND_[A-Z0-9]{8,32}',
                                         self.private_boundary_receipt_id) or
                not _optional_identifier(r'AUTH_[A-Z0-9]{8,32}',
                                         self.authorization_receipt_id) or
                not _optional_identifier(r'[0-9a-f]{64}', self.corpus_digest) or
                not _optional_identifier(r'[0-9a-f]{64}', self.label_set_digest)):
            raise ValueError('invalid_provider_qualification_evidence')


def default_provider_qualification_policy():
    """Return the adopted conservative protocol for a candidate provider."""
    return ProviderQualificationPolicy(
        'QPOL_PROVIDERQUAL01', '1.0.0', 'PRV_CANDIDATE01',
        'DATA_CANDIDATE01', 'atlas.candidate_extractor@1.0.0')


def assess_provider_qualification(policy, evidence=None, *, now=None):
    """Return a redacted technical decision; never grant release authority."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(policy, ProviderQualificationPolicy) or
            not isinstance(now, datetime) or now.tzinfo is None or
            (evidence is not None and
             not isinstance(evidence, ProviderQualificationEvidence))):
        raise ValueError('invalid_provider_qualification_request')

    if evidence is None:
        codes = [
            'private_boundary_evidence_missing',
            'authorization_evidence_missing',
            'representative_corpus_missing',
            'independent_review_missing',
            'measured_quality_missing',
        ]
        return _report(policy, None, codes, now)

    codes = []
    for code, actual, expected in (
        ('provider_identity_mismatch', evidence.provider_id, policy.provider_id),
        ('dataset_identity_mismatch', evidence.dataset_id, policy.dataset_id),
        ('extractor_version_mismatch', evidence.extractor_version,
         policy.extractor_version),
    ):
        if actual != expected:
            codes.append(code)
    if evidence.scope != 'private_authorized':
        codes.append('synthetic_evidence_only')
    if evidence.private_boundary_receipt_id is None:
        codes.append('private_boundary_evidence_missing')
    if evidence.authorization_receipt_id is None:
        codes.append('authorization_evidence_missing')
    if evidence.corpus_digest is None or evidence.label_set_digest is None:
        codes.append('representative_corpus_missing')
    if (len(evidence.reviewer_ids) < policy.minimum_independent_reviewer_count or
            len(set(evidence.reviewer_ids)) != len(evidence.reviewer_ids)):
        codes.append('independent_review_missing')
    if evidence.document_count < policy.minimum_document_count:
        codes.append('insufficient_document_count')
    if evidence.field_check_count < policy.minimum_field_check_count:
        codes.append('insufficient_field_check_count')
    exact_rate = (Decimal(evidence.exact_match_count) /
                  Decimal(evidence.field_check_count)
                  if evidence.field_check_count else None)
    if exact_rate is None or exact_rate < policy.minimum_exact_match_rate:
        codes.append('exact_match_rate_below_threshold')
    supported = set(evidence.supported_formats)
    covered = supported.intersection(evidence.tested_formats)
    coverage_rate = (Decimal(len(covered)) / Decimal(len(supported))
                     if supported else None)
    if (coverage_rate is None or
            coverage_rate < policy.minimum_format_coverage_rate or
            set(evidence.tested_formats) - supported):
        codes.append('format_coverage_incomplete')
    if evidence.critical_error_count > policy.maximum_critical_error_count:
        codes.append('critical_error_limit_exceeded')
    if evidence.semantic_mismatch_count > policy.maximum_semantic_mismatch_count:
        codes.append('semantic_mismatch_limit_exceeded')
    if evidence.evaluated_at > now:
        codes.append('qualification_evaluation_in_future')
    if evidence.expires_at <= now:
        codes.append('qualification_evidence_expired')
    return _report(policy, evidence, codes, now, exact_rate, coverage_rate)


def _report(policy, evidence, codes, now, exact_rate=None, coverage_rate=None):
    qualified = not codes and evidence is not None
    return {
        'schema_version': 1,
        'status': 'qualified_private' if qualified else 'blocked',
        'codes': ['private_provider_qualified'] if qualified else codes,
        'policy_version': policy.policy_version,
        'evidence_scope': evidence.scope if evidence else 'none',
        'document_count': evidence.document_count if evidence else 0,
        'field_check_count': evidence.field_check_count if evidence else 0,
        'exact_match_rate': str(exact_rate) if exact_rate is not None else None,
        'format_coverage_rate': (str(coverage_rate)
                                 if coverage_rate is not None else None),
        'critical_error_count': evidence.critical_error_count if evidence else None,
        'semantic_mismatch_count': (evidence.semantic_mismatch_count
                                    if evidence else None),
        'evaluated_at': now.isoformat(),
        'release_authorized': False,
        'qualification_boundary': (
            'technical provider qualification only; founder release, legal, '
            'security and production approval remain separate'),
    }
