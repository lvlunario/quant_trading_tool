"""Point-in-time macroeconomic release and revision contracts."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import re
from typing import Literal
from urllib.parse import urlsplit

from .reference import DataRightsRecord, UseCase, check_data_rights


MacroUnit = Literal['count', 'index', 'money', 'percent', 'rate']
MacroFrequency = Literal['daily', 'weekly', 'monthly', 'quarterly', 'annual']
SeasonalAdjustment = Literal[
    'seasonally_adjusted', 'not_seasonally_adjusted', 'not_applicable'
]
MissingReason = Literal['not_reported', 'source_missing', 'suppressed']


def _matches(pattern: str, value) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _safe_label(value: str) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= 160 and
            value == value.strip() and all(character.isprintable() for character in value))


def _https_uri(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and
            parsed.username is None and parsed.password is None and
            not parsed.fragment)


@dataclass(frozen=True)
class MacroReleaseRecord:
    """One published vintage for one macro series and reporting period."""

    release_id: str
    macro_series_id: str
    provider_id: str
    dataset_id: str
    name: str
    unit: MacroUnit
    frequency: MacroFrequency
    seasonal_adjustment: SeasonalAdjustment
    period_start: date
    period_end: date
    revision: int
    available_at: datetime
    observed_at: datetime
    value: Decimal | None
    missing_reason: MissingReason | None
    source_uri: str
    source_sha256: str
    transform_version: str

    def __post_init__(self):
        identifiers = (
            ('release_id', r'MREL_[A-Z0-9]{12,32}', self.release_id),
            ('macro_series_id', r'MAC_[A-Z0-9]{12,32}', self.macro_series_id),
            ('provider_id', r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            ('dataset_id', r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
        )
        for name, pattern, value in identifiers:
            if not _matches(pattern, value):
                raise ValueError(f'invalid_{name}')
        if not _safe_label(self.name):
            raise ValueError('invalid_macro_name')
        if self.unit not in ('count', 'index', 'money', 'percent', 'rate'):
            raise ValueError('invalid_macro_unit')
        if self.frequency not in ('daily', 'weekly', 'monthly', 'quarterly', 'annual'):
            raise ValueError('invalid_macro_frequency')
        if self.seasonal_adjustment not in ('seasonally_adjusted',
                                             'not_seasonally_adjusted',
                                             'not_applicable'):
            raise ValueError('invalid_seasonal_adjustment')
        if (type(self.period_start) is not date or type(self.period_end) is not date or
                self.period_start > self.period_end):
            raise ValueError('invalid_macro_period')
        if (isinstance(self.revision, bool) or not isinstance(self.revision, int) or
                not 0 <= self.revision <= 1_000_000):
            raise ValueError('invalid_macro_revision')
        if (not isinstance(self.available_at, datetime) or self.available_at.tzinfo is None or
                not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None or
                self.available_at > self.observed_at):
            raise ValueError('invalid_macro_times')
        if self.value is not None:
            if not isinstance(self.value, Decimal) or not self.value.is_finite():
                raise ValueError('invalid_macro_value')
            if self.missing_reason is not None:
                raise ValueError('invalid_macro_missing_state')
        elif self.missing_reason not in ('not_reported', 'source_missing', 'suppressed'):
            raise ValueError('invalid_macro_missing_state')
        if not _https_uri(self.source_uri):
            raise ValueError('invalid_source_uri')
        if not _matches(r'[0-9a-f]{64}', self.source_sha256):
            raise ValueError('invalid_source_hash')
        if not _matches(r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
                        self.transform_version):
            raise ValueError('invalid_transform_version')


@dataclass(frozen=True)
class MacroVintageSelection:
    status: Literal['selected', 'missing']
    code: str
    release_id: str | None
    revision: int | None
    available_at: datetime | None
    value: Decimal | None
    missing_reason: MissingReason | None


@dataclass(frozen=True)
class MacroReadiness:
    status: Literal['ready', 'blocked']
    codes: tuple[str, ...]
    release_id: str | None
    value: Decimal | None


def select_macro_vintage(records: list[MacroReleaseRecord], *, macro_series_id: str,
                         period_end: date, decision_at: datetime,
                         now=None) -> MacroVintageSelection:
    """Select the latest revision that was public at a decision timestamp."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(records, list) or len(records) > 10000 or
            not _matches(r'MAC_[A-Z0-9]{12,32}', macro_series_id) or
            type(period_end) is not date or
            not isinstance(decision_at, datetime) or decision_at.tzinfo is None or
            not isinstance(now, datetime) or now.tzinfo is None or decision_at > now):
        raise ValueError('invalid_macro_selection_request')
    if any(not isinstance(record, MacroReleaseRecord) for record in records):
        raise ValueError('invalid_macro_release_record')
    if any(record.observed_at > now for record in records):
        raise ValueError('future_macro_observation')
    release_ids = [record.release_id for record in records]
    if len(set(release_ids)) != len(release_ids):
        raise ValueError('duplicate_macro_release_id')
    series = [record for record in records if record.macro_series_id == macro_series_id]
    if not series:
        return MacroVintageSelection('missing', 'unknown_macro_series',
                                     None, None, None, None, None)
    period = [record for record in series if record.period_end == period_end]
    if not period:
        return MacroVintageSelection('missing', 'unknown_macro_period',
                                     None, None, None, None, None)
    identities = {(record.provider_id, record.dataset_id, record.name, record.unit,
                   record.frequency, record.seasonal_adjustment, record.period_start,
                   record.period_end) for record in period}
    if len(identities) != 1:
        raise ValueError('macro_series_identity_conflict')
    revisions = [record.revision for record in period]
    if len(set(revisions)) != len(revisions):
        raise ValueError('duplicate_macro_revision')
    ordered = sorted(period, key=lambda record: record.revision)
    if any(current.available_at > following.available_at
           for current, following in zip(ordered, ordered[1:])):
        raise ValueError('macro_revision_time_conflict')
    eligible = [record for record in period if record.available_at <= decision_at]
    if not eligible:
        return MacroVintageSelection('missing', 'macro_not_yet_available',
                                     None, None, None, None, None)
    chosen = max(eligible, key=lambda record: (record.available_at, record.revision))
    return MacroVintageSelection('selected', 'latest_available_macro_vintage',
                                 chosen.release_id, chosen.revision, chosen.available_at,
                                 chosen.value, chosen.missing_reason)


def assess_macro_input(records: list[MacroReleaseRecord], rights: list[DataRightsRecord], *,
                       macro_series_id: str, period_end: date, decision_at: datetime,
                       use_case: UseCase, now=None) -> MacroReadiness:
    """Release a macro value only after point-in-time and rights checks pass."""
    now = now or datetime.now(timezone.utc)
    selection = select_macro_vintage(records, macro_series_id=macro_series_id,
                                     period_end=period_end, decision_at=decision_at,
                                     now=now)
    if selection.status != 'selected':
        return MacroReadiness('blocked', (selection.code,), None, None)
    selected = next(record for record in records
                    if record.release_id == selection.release_id)
    permission = check_data_rights(rights, provider_id=selected.provider_id,
                                   dataset_id=selected.dataset_id,
                                   use_case=use_case, at=now)
    if not permission.allowed:
        return MacroReadiness('blocked', (f'rights_{permission.code}',), None, None)
    if selection.value is None:
        return MacroReadiness('blocked',
                              (f'macro_value_{selection.missing_reason}',), None, None)
    return MacroReadiness('ready', ('point_in_time_macro_rights_passed',),
                          selection.release_id, selection.value)
