"""Versioned metric payload binding, separate from research permission gates."""
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
import json

from .metrics import MetricValue
from .provenance import ObservationRecord


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
