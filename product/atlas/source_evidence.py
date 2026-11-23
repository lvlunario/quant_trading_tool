"""Immutable research-source records and observation binding checks.

The contract proves internal consistency and point-in-time availability. It does
not authenticate a publisher, establish source accuracy, or grant data rights.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Literal
from urllib.parse import urlsplit

from .provenance import ObservationRecord


SourceKind = Literal[
    'issuer_filing', 'issuer_release', 'regulator_filing', 'exchange_notice',
    'licensed_dataset'
]
ContentType = Literal['application/json', 'application/pdf', 'text/csv', 'text/html']


def _matches(pattern: str, value) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _https_uri(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and
            not parsed.fragment)


@dataclass(frozen=True)
class ResearchSourceRecord:
    """Metadata for exact bytes retrieved from an instrument-level source."""

    document_id: str
    instrument_id: str
    provider_id: str
    dataset_id: str
    source_kind: SourceKind
    content_type: ContentType
    published_at: datetime
    available_at: datetime
    retrieved_at: datetime
    source_uri: str
    source_sha256: str

    def __post_init__(self):
        identifiers = (
            ('document_id', r'DOC_[A-Z0-9]{12,32}', self.document_id),
            ('instrument_id', r'INS_[A-Z0-9]{12,32}', self.instrument_id),
            ('provider_id', r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            ('dataset_id', r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
        )
        for name, pattern, value in identifiers:
            if not _matches(pattern, value):
                raise ValueError(f'invalid_{name}')
        if self.source_kind not in ('issuer_filing', 'issuer_release',
                                    'regulator_filing', 'exchange_notice',
                                    'licensed_dataset'):
            raise ValueError('invalid_source_kind')
        if self.content_type not in ('application/json', 'application/pdf',
                                     'text/csv', 'text/html'):
            raise ValueError('invalid_content_type')
        times = (self.published_at, self.available_at, self.retrieved_at)
        if any(not isinstance(value, datetime) or value.tzinfo is None for value in times):
            raise ValueError('invalid_source_times')
        if not self.published_at <= self.available_at <= self.retrieved_at:
            raise ValueError('invalid_source_times')
        if not _https_uri(self.source_uri):
            raise ValueError('invalid_source_uri')
        if not _matches(r'[0-9a-f]{64}', self.source_sha256):
            raise ValueError('invalid_source_hash')


@dataclass(frozen=True)
class SourceBindingDecision:
    status: Literal['ready', 'blocked']
    codes: tuple[str, ...]
    document_id: str | None


def assess_source_binding(source: ResearchSourceRecord, observation: ObservationRecord, *,
                          now=None) -> SourceBindingDecision:
    """Bind an observation to exact, timely source bytes without guessing."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(source, ResearchSourceRecord) or
            not isinstance(observation, ObservationRecord) or
            not isinstance(now, datetime) or now.tzinfo is None):
        raise ValueError('invalid_source_binding_request')
    if source.retrieved_at > now:
        return SourceBindingDecision('blocked', ('source_future_retrieval',), None)

    checks = (
        ('source_instrument_mismatch', source.instrument_id, observation.instrument_id),
        ('source_provider_mismatch', source.provider_id, observation.provider_id),
        ('source_dataset_mismatch', source.dataset_id, observation.dataset_id),
        ('source_uri_mismatch', source.source_uri, observation.source_uri),
        ('source_hash_mismatch', source.source_sha256, observation.source_sha256),
        ('source_availability_mismatch', source.available_at, observation.available_at),
    )
    codes = [code for code, actual, expected in checks if actual != expected]
    if source.retrieved_at > observation.observed_at:
        codes.append('source_retrieved_after_observation')
    if codes:
        return SourceBindingDecision('blocked', tuple(codes), None)
    return SourceBindingDecision('ready', ('exact_source_binding_passed',),
                                 source.document_id)
