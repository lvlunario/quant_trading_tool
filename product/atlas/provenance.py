"""Point-in-time provenance records for leakage-resistant research."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Literal
from urllib.parse import urlsplit

from .reference import (DataRightsRecord, SecurityRecord, UseCase, check_data_rights,
                        verify_instrument)


def _matches(pattern: str, value) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _https_uri(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and not parsed.fragment)


@dataclass(frozen=True)
class ObservationRecord:
    """Metadata binding one research value revision to its evidence."""

    observation_id: str
    series_id: str
    revision: int
    instrument_id: str
    provider_id: str
    dataset_id: str
    metric_id: str
    as_of: date
    available_at: datetime
    observed_at: datetime
    source_uri: str
    source_sha256: str
    payload_sha256: str
    transform_version: str

    def __post_init__(self):
        patterns = (
            ('observation_id', r'OBS_[A-Z0-9]{12,32}', self.observation_id),
            ('series_id', r'SER_[A-Z0-9]{12,32}', self.series_id),
            ('instrument_id', r'INS_[A-Z0-9]{12,32}', self.instrument_id),
            ('provider_id', r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            ('dataset_id', r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
            ('metric_id', r'MET_[A-Z0-9_]{4,40}', self.metric_id),
        )
        for name, pattern, value in patterns:
            if not _matches(pattern, value):
                raise ValueError(f'invalid_{name}')
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or not 0 <= self.revision <= 1_000_000:
            raise ValueError('invalid_revision')
        if type(self.as_of) is not date:
            raise ValueError('invalid_as_of')
        if (not isinstance(self.available_at, datetime) or self.available_at.tzinfo is None or
                not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None or
                self.available_at > self.observed_at):
            raise ValueError('invalid_provenance_times')
        if not _https_uri(self.source_uri):
            raise ValueError('invalid_source_uri')
        if not _matches(r'[0-9a-f]{64}', self.source_sha256):
            raise ValueError('invalid_source_hash')
        if not _matches(r'[0-9a-f]{64}', self.payload_sha256):
            raise ValueError('invalid_payload_hash')
        if not _matches(r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
                        self.transform_version):
            raise ValueError('invalid_transform_version')


@dataclass(frozen=True)
class ObservationSelection:
    status: Literal['selected', 'missing']
    code: str
    observation_id: str | None
    revision: int | None
    available_at: datetime | None
    payload_sha256: str | None


@dataclass(frozen=True)
class ResearchReadiness:
    status: Literal['ready', 'blocked']
    codes: tuple[str, ...]
    observation_id: str | None
    payload_sha256: str | None


def select_point_in_time(records: list[ObservationRecord], *, series_id: str,
                         decision_at: datetime, now=None) -> ObservationSelection:
    """Select only the latest revision available at a historical decision time."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(records, list) or len(records) > 10000 or
            not _matches(r'SER_[A-Z0-9]{12,32}', series_id) or
            not isinstance(decision_at, datetime) or decision_at.tzinfo is None or
            not isinstance(now, datetime) or now.tzinfo is None or decision_at > now):
        raise ValueError('invalid_point_in_time_request')
    if any(not isinstance(record, ObservationRecord) for record in records):
        raise ValueError('invalid_observation_record')
    if any(record.observed_at > now for record in records):
        raise ValueError('future_observation')
    all_observation_ids = [record.observation_id for record in records]
    if len(set(all_observation_ids)) != len(all_observation_ids):
        raise ValueError('duplicate_observation_id')
    selected_series = [record for record in records if record.series_id == series_id]
    if not selected_series:
        return ObservationSelection('missing', 'unknown_series', None, None, None, None)
    identities = {(record.instrument_id, record.provider_id, record.dataset_id,
                   record.metric_id, record.as_of) for record in selected_series}
    if len(identities) != 1:
        raise ValueError('series_identity_conflict')
    revisions = [record.revision for record in selected_series]
    if len(set(revisions)) != len(revisions):
        raise ValueError('duplicate_revision')
    ordered = sorted(selected_series, key=lambda record: record.revision)
    if any(current.available_at > following.available_at
           for current, following in zip(ordered, ordered[1:])):
        raise ValueError('revision_time_conflict')
    eligible = [record for record in selected_series if record.available_at <= decision_at]
    if not eligible:
        return ObservationSelection('missing', 'not_yet_available', None, None, None, None)
    chosen = max(eligible, key=lambda record: (record.available_at, record.revision))
    return ObservationSelection('selected', 'latest_available_revision',
                                chosen.observation_id, chosen.revision,
                                chosen.available_at, chosen.payload_sha256)


def assess_research_input(observations: list[ObservationRecord],
                          securities: list[SecurityRecord], rights: list[DataRightsRecord], *,
                          series_id: str, decision_at: datetime, use_case: UseCase,
                          now=None) -> ResearchReadiness:
    """Combine point-in-time, effective-identity and current-rights gates."""
    now = now or datetime.now(timezone.utc)
    selection = select_point_in_time(observations, series_id=series_id,
                                     decision_at=decision_at, now=now)
    if selection.status != 'selected':
        return ResearchReadiness('blocked', (f'observation_{selection.code}',), None, None)
    selected = next(record for record in observations
                    if record.observation_id == selection.observation_id)
    identity = verify_instrument(securities, instrument_id=selected.instrument_id,
                                 on_date=selected.as_of, now=now)
    permission = check_data_rights(rights, provider_id=selected.provider_id,
                                   dataset_id=selected.dataset_id, use_case=use_case, at=now)
    codes = []
    if identity.status != 'resolved':
        codes.append(f'identity_{identity.code}')
    if not permission.allowed:
        codes.append(f'rights_{permission.code}')
    if codes:
        return ResearchReadiness('blocked', tuple(codes), None, None)
    return ResearchReadiness('ready', ('point_in_time_identity_rights_passed',),
                             selected.observation_id, selected.payload_sha256)
