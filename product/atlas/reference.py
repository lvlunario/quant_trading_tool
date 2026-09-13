"""Effective-dated security identity and dataset-rights gates.

Records are evidence contracts, not a populated security master or a statement
that any provider license exists.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Literal
from urllib.parse import urlsplit


SecurityClass = Literal[
    'common_stock', 'preferred_stock', 'depositary_receipt', 'fund', 'other_listed'
]
UseCase = Literal['internal_research', 'customer_display', 'model_training', 'redistribution']


def _matches(pattern: str, value) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _https_uri(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and not parsed.fragment)


def _safe_label(value: str) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= 200 and
            value == value.strip() and all(character.isprintable() for character in value))


@dataclass(frozen=True)
class SecurityRecord:
    instrument_id: str
    issuer_id: str
    issuer_name: str
    security_name: str
    exchange_mic: str
    currency: Literal['USD']
    security_class: SecurityClass
    symbol: str
    effective_from: date
    effective_to: date | None
    source_uri: str
    observed_at: datetime

    def __post_init__(self):
        if not _matches(r'INS_[A-Z0-9]{12,32}', self.instrument_id):
            raise ValueError('invalid_instrument_id')
        if not _matches(r'ISS_[A-Z0-9]{12,32}', self.issuer_id):
            raise ValueError('invalid_issuer_id')
        if not _safe_label(self.issuer_name) or not _safe_label(self.security_name):
            raise ValueError('invalid_security_label')
        if not _matches(r'[A-Z0-9]{4}', self.exchange_mic):
            raise ValueError('invalid_exchange_mic')
        if self.currency != 'USD':
            raise ValueError('unsupported_currency')
        if self.security_class not in ('common_stock', 'preferred_stock',
                                       'depositary_receipt', 'fund', 'other_listed'):
            raise ValueError('invalid_security_class')
        if not _matches(r'[A-Z][A-Z0-9.-]{0,15}', self.symbol):
            raise ValueError('invalid_symbol')
        if (type(self.effective_from) is not date or
                (self.effective_to is not None and
                 (type(self.effective_to) is not date or
                  self.effective_to <= self.effective_from))):
            raise ValueError('invalid_effective_period')
        if not _https_uri(self.source_uri):
            raise ValueError('invalid_source_uri')
        if not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None:
            raise ValueError('invalid_observed_at')


@dataclass(frozen=True)
class SecurityResolution:
    status: Literal['resolved', 'missing', 'ambiguous']
    code: str
    instrument_id: str | None


def resolve_security(records: list[SecurityRecord], *, symbol: str, exchange_mic: str,
                     on_date: date, now=None) -> SecurityResolution:
    """Resolve a symbol/MIC/date without guessing across identities."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(records, list) or len(records) > 10000 or
            not _matches(r'[A-Z][A-Z0-9.-]{0,15}', symbol) or
            not _matches(r'[A-Z0-9]{4}', exchange_mic) or
            type(on_date) is not date or not isinstance(now, datetime) or
            now.tzinfo is None):
        raise ValueError('invalid_resolution_request')
    if any(not isinstance(record, SecurityRecord) for record in records):
        raise ValueError('invalid_security_record')
    if any(record.observed_at > now for record in records):
        raise ValueError('future_security_evidence')
    stable_identities = {}
    for record in records:
        identity = (record.issuer_id, record.currency, record.security_class)
        stable_identities.setdefault(record.instrument_id, set()).add(identity)
    if any(len(identities) > 1 for identities in stable_identities.values()):
        raise ValueError('instrument_identity_conflict')
    candidates = [
        record for record in records
        if record.symbol == symbol and record.exchange_mic == exchange_mic and
        record.effective_from <= on_date and
        (record.effective_to is None or on_date < record.effective_to)
    ]
    if not candidates:
        return SecurityResolution('missing', 'no_effective_identity', None)
    identities = {record.instrument_id for record in candidates}
    if len(identities) > 1:
        return SecurityResolution('ambiguous', 'overlapping_identities', None)
    return SecurityResolution('resolved', 'effective_identity', candidates[0].instrument_id)


@dataclass(frozen=True)
class DataRightsRecord:
    provider_id: str
    dataset_id: str
    status: Literal['pending', 'verified', 'prohibited']
    permitted_uses: tuple[UseCase, ...]
    terms_uri: str
    evidence_sha256: str
    reviewed_at: datetime
    valid_until: datetime | None

    def __post_init__(self):
        valid_uses = {'internal_research', 'customer_display', 'model_training', 'redistribution'}
        if not _matches(r'PRV_[A-Z0-9]{8,24}', self.provider_id):
            raise ValueError('invalid_provider_id')
        if not _matches(r'DATA_[A-Z0-9]{8,32}', self.dataset_id):
            raise ValueError('invalid_dataset_id')
        if self.status not in ('pending', 'verified', 'prohibited'):
            raise ValueError('invalid_rights_status')
        if (not isinstance(self.permitted_uses, tuple) or
                any(not isinstance(use, str) for use in self.permitted_uses) or
                set(self.permitted_uses) - valid_uses or
                len(set(self.permitted_uses)) != len(self.permitted_uses) or
                (self.status == 'verified' and not self.permitted_uses) or
                (self.status != 'verified' and self.permitted_uses)):
            raise ValueError('invalid_permitted_uses')
        if not _https_uri(self.terms_uri):
            raise ValueError('invalid_terms_uri')
        if not _matches(r'[0-9a-f]{64}', self.evidence_sha256):
            raise ValueError('invalid_rights_evidence_hash')
        if not isinstance(self.reviewed_at, datetime) or self.reviewed_at.tzinfo is None:
            raise ValueError('invalid_reviewed_at')
        if (self.valid_until is not None and
                (not isinstance(self.valid_until, datetime) or self.valid_until.tzinfo is None or
                 self.valid_until <= self.reviewed_at)):
            raise ValueError('invalid_rights_period')


@dataclass(frozen=True)
class RightsDecision:
    allowed: bool
    code: str
    evidence_sha256: str | None


def check_data_rights(records: list[DataRightsRecord], *, provider_id: str, dataset_id: str,
                      use_case: UseCase, at=None) -> RightsDecision:
    """Fail closed unless the latest applicable evidence explicitly permits use."""
    at = at or datetime.now(timezone.utc)
    valid_uses = {'internal_research', 'customer_display', 'model_training', 'redistribution'}
    if (not isinstance(records, list) or len(records) > 10000 or
            not _matches(r'PRV_[A-Z0-9]{8,24}', provider_id) or
            not _matches(r'DATA_[A-Z0-9]{8,32}', dataset_id) or
            use_case not in valid_uses or not isinstance(at, datetime) or at.tzinfo is None):
        raise ValueError('invalid_rights_request')
    if any(not isinstance(record, DataRightsRecord) for record in records):
        raise ValueError('invalid_rights_record')
    matching = [record for record in records
                if record.provider_id == provider_id and record.dataset_id == dataset_id and
                record.reviewed_at <= at]
    if not matching:
        return RightsDecision(False, 'missing_evidence', None)
    latest_at = max(record.reviewed_at for record in matching)
    latest = [record for record in matching if record.reviewed_at == latest_at]
    signatures = {(record.status, record.permitted_uses, record.evidence_sha256,
                   record.valid_until) for record in latest}
    if len(signatures) != 1:
        return RightsDecision(False, 'ambiguous_evidence', None)
    record = latest[0]
    if record.valid_until is not None and at >= record.valid_until:
        return RightsDecision(False, 'expired_evidence', record.evidence_sha256)
    if record.status == 'prohibited':
        return RightsDecision(False, 'prohibited', record.evidence_sha256)
    if record.status != 'verified':
        return RightsDecision(False, 'pending_evidence', record.evidence_sha256)
    if use_case not in record.permitted_uses:
        return RightsDecision(False, 'use_not_permitted', record.evidence_sha256)
    return RightsDecision(True, 'explicitly_permitted', record.evidence_sha256)
