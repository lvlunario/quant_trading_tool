"""Versioned metric payload binding, separate from research permission gates."""
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
import json

from .metrics import MetricValue
from .provenance import ObservationRecord, assess_research_input


@dataclass(frozen=True)
class MetricPayload:
    metric: MetricValue
    period_start: date
    period_end: date

    def __post_init__(self):
        if not isinstance(self.metric, MetricValue):
            raise ValueError('invalid_metric_payload')
        if (type(self.period_start) is not date or type(self.period_end) is not date or
                self.period_start > self.period_end):
            raise ValueError('invalid_reporting_period')
        if self.metric.definition.period == 'instant' and self.period_start != self.period_end:
            raise ValueError('instant_period_must_be_single_date')

    def canonical_bytes(self) -> bytes:
        """V1 UTF-8 JSON, sorted keys; Decimal representation retained exactly."""
        return json.dumps({
            'schema_version': 1,
            'definition': asdict(self.metric.definition),
            'value': None if self.metric.value is None else str(self.metric.value),
            'missing_reason': self.metric.missing_reason,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
        }, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')

    @property
    def payload_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


def verify_metric_binding(payload: MetricPayload, observation: ObservationRecord) -> None:
    """Detect drift between numeric payload and claimed observation metadata."""
    if not isinstance(payload, MetricPayload) or not isinstance(observation, ObservationRecord):
        raise ValueError('invalid_metric_binding')
    definition = payload.metric.definition
    if definition.metric_id != observation.metric_id:
        raise ValueError('metric_identity_mismatch')
    if definition.transform_version != observation.transform_version:
        raise ValueError('metric_transform_mismatch')
    if payload.period_end != observation.as_of:
        raise ValueError('metric_as_of_mismatch')
    if payload.payload_sha256 != observation.payload_sha256:
        raise ValueError('metric_payload_hash_mismatch')


@dataclass(frozen=True)
class MetricReadiness:
    status: str
    codes: tuple[str, ...]
    observation_id: str | None = None
    payload: MetricPayload | None = None


def assess_metric_input(payload, observations, securities, rights, *,
                        series_id, decision_at, use_case, now=None) -> MetricReadiness:
    """Release a numeric payload only after metadata and binding checks pass."""
    if not isinstance(payload, MetricPayload):
        raise ValueError('invalid_metric_payload')
    metadata = assess_research_input(observations, securities, rights,
        series_id=series_id, decision_at=decision_at, use_case=use_case, now=now)
    if metadata.status != 'ready':
        return MetricReadiness('blocked', metadata.codes)
    selected = next(record for record in observations
                    if record.observation_id == metadata.observation_id)
    try:
        verify_metric_binding(payload, selected)
    except ValueError as error:
        return MetricReadiness('blocked', (str(error),))
    if payload.metric.value is None:
        return MetricReadiness('blocked', ('metric_unavailable',))
    return MetricReadiness('ready', ('metadata_binding_numeric_passed',),
                           selected.observation_id, payload)
