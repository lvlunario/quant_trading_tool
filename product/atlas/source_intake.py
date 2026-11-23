"""Bounded, permission-gated intake for exact research-source bytes.

This module does not fetch URLs, authenticate publishers, extract metrics, or
persist document content. It converts already-retrieved bytes into an immutable
metadata record only after the requested use is explicitly permitted.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal

from .reference import DataRightsRecord, UseCase, check_data_rights
from .source_evidence import ContentType, ResearchSourceRecord, SourceKind


MAX_SOURCE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class SourceIntakeRequest:
    document_id: str
    instrument_id: str
    provider_id: str
    dataset_id: str
    source_kind: SourceKind
    content_type: ContentType
    published_at: datetime
    available_at: datetime
    source_uri: str


@dataclass(frozen=True)
class SourceIntakeResult:
    status: Literal['ready', 'blocked']
    codes: tuple[str, ...]
    record: ResearchSourceRecord | None
    byte_count: int


def _content_code(content: bytes, content_type: str) -> str | None:
    if content_type == 'application/pdf':
        return None if content.startswith(b'%PDF-') else 'source_content_signature_mismatch'
    if content_type in ('application/json', 'text/csv', 'text/html'):
        try:
            decoded = content.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            return 'source_encoding_invalid'
        if '\x00' in decoded:
            return 'source_encoding_invalid'
    return None


def intake_research_source(content: bytes, request: SourceIntakeRequest,
                           rights: list[DataRightsRecord], *, use_case: UseCase,
                           now=None) -> SourceIntakeResult:
    """Create a hash-bound source record without retaining source content."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(content, bytes) or
            not isinstance(request, SourceIntakeRequest) or
            not isinstance(now, datetime) or now.tzinfo is None):
        raise ValueError('invalid_source_intake_request')
    byte_count = len(content)
    if byte_count == 0:
        return SourceIntakeResult('blocked', ('source_empty',), None, byte_count)
    if byte_count > MAX_SOURCE_BYTES:
        return SourceIntakeResult('blocked', ('source_too_large',), None, byte_count)

    try:
        permission = check_data_rights(
            rights, provider_id=request.provider_id, dataset_id=request.dataset_id,
            use_case=use_case, at=now)
    except ValueError:
        return SourceIntakeResult(
            'blocked', ('source_contract_invalid',), None, byte_count)
    if not permission.allowed:
        return SourceIntakeResult(
            'blocked', (f'rights_{permission.code}',), None, byte_count)

    content_code = _content_code(content, request.content_type)
    if content_code:
        return SourceIntakeResult('blocked', (content_code,), None, byte_count)

    try:
        record = ResearchSourceRecord(
            request.document_id, request.instrument_id, request.provider_id,
            request.dataset_id, request.source_kind, request.content_type,
            request.published_at, request.available_at, now, request.source_uri,
            sha256(content).hexdigest())
    except ValueError:
        return SourceIntakeResult(
            'blocked', ('source_contract_invalid',), None, byte_count)
    return SourceIntakeResult(
        'ready', ('rights_explicitly_permitted', 'source_bytes_captured'),
        record, byte_count)
