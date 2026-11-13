"""Explicit metric semantics; no implicit unit or period conversion."""
from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    definition_version: str
    formula: str
    unit: str
    currency: str | None
    period: str
    null_policy: str
    transform_version: str

    def __post_init__(self):
        for value, pattern in (
            (self.metric_id, r'MET_[A-Z0-9_]{4,40}'),
            (self.definition_version, r'\d{1,6}\.\d{1,6}\.\d{1,6}'),
            (self.transform_version, r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}'),
        ):
            if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
                raise ValueError('invalid_metric_identifier_or_version')
        if not isinstance(self.formula, str) or not self.formula.strip() or len(self.formula) > 1000:
            raise ValueError('invalid_metric_formula')
        if self.unit not in ('money', 'money_per_share', 'ratio', 'count'):
            raise ValueError('unsupported_metric_unit')
        monetary = self.unit in ('money', 'money_per_share')
        if (monetary and self.currency != 'USD') or (not monetary and self.currency is not None):
            raise ValueError('incompatible_metric_currency')
        if self.period not in ('instant', 'quarter', 'annual', 'ttm'):
            raise ValueError('unsupported_metric_period')
        if self.null_policy not in ('missing', 'not_meaningful'):
            raise ValueError('unsupported_null_policy')


@dataclass(frozen=True)
class MetricValue:
    definition: MetricDefinition
    value: Decimal | None
    missing_reason: str | None = None

    def __post_init__(self):
        if not isinstance(self.definition, MetricDefinition):
            raise ValueError('invalid_metric_definition')
        if self.value is None:
            if self.missing_reason not in ('missing_source', 'not_meaningful'):
                raise ValueError('missing_metric_reason_required')
            if self.missing_reason == 'not_meaningful' and self.definition.null_policy != 'not_meaningful':
                raise ValueError('incompatible_null_reason')
        elif (not isinstance(self.value, Decimal) or not self.value.is_finite() or
              self.missing_reason is not None):
            raise ValueError('invalid_metric_value')


def require_compatible(left: MetricValue, right: MetricValue) -> None:
    """Reject mismatched definitions or missing operands before downstream math."""
    if not isinstance(left, MetricValue) or not isinstance(right, MetricValue):
        raise ValueError('invalid_metric_operand')
    if left.definition != right.definition:
        raise ValueError('incompatible_metric_definitions')
    if left.value is None or right.value is None:
        raise ValueError('metric_unavailable')
