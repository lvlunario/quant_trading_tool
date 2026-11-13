"""Registered validation-only metrics for the invented M3 experiment.

The final holdout never enters this module. Receipts expose only synthetic
validation metrics and identity fields: no prices, cash, shares or fill rows.
They are engineering evidence and cannot establish investable performance.
"""
from dataclasses import dataclass
from decimal import Decimal

from .evaluation import FoldSpec, SampleWindow, plan_fold
from .evaluation_metrics import EvaluationMetrics, calculate_evaluation_metrics
from .experiment_registry import (
    ExperimentConfig, ExperimentManifest, ExperimentOutputReceipt,
    bind_synthetic_output, register_experiment,
)
from .synthetic_execution import ExecutionPolicy, TargetState
from .synthetic_series import SyntheticSeries
from .validation_run import _REGISTERED_WINDOWS, _target_at


SCHEMA_VERSION = 1


def _decimal(value: Decimal) -> str:
    return format(value, 'f')


@dataclass(frozen=True)
class ValidationMetricFoldReceipt:
    fold_id: str
    validation_start: int
    validation_end: int
    eligible_decision_count: int
    candidate_base: EvaluationMetrics
    comparator_base: EvaluationMetrics
    candidate_adverse: EvaluationMetrics
    comparator_adverse: EvaluationMetrics

    def __post_init__(self):
        metrics = (
            self.candidate_base, self.comparator_base,
            self.candidate_adverse, self.comparator_adverse)
        if (self.fold_id not in ('fold-1', 'fold-2') or
                type(self.validation_start) is not int or
                type(self.validation_end) is not int or
                self.validation_start >= self.validation_end or
                type(self.eligible_decision_count) is not int or
                self.eligible_decision_count < 1 or
                any(not isinstance(row, EvaluationMetrics) or
                    row.marked_session_count !=
                    self.validation_end - self.validation_start
                    for row in metrics)):
            raise ValueError('invalid_validation_metric_fold')

    def canonical_lines(self) -> tuple[str, ...]:
        lines = [
            f'fold={self.fold_id}|{self.validation_start}|{self.validation_end}|'
            f'{self.eligible_decision_count}'
        ]
        for label, metrics in (
                ('candidate_base', self.candidate_base),
                ('comparator_base', self.comparator_base),
                ('candidate_adverse', self.candidate_adverse),
                ('comparator_adverse', self.comparator_adverse)):
            lines.append(
                f'metrics={self.fold_id}|{label}|'
                f'{_decimal(metrics.gross_cumulative_return)}|'
                f'{_decimal(metrics.net_cumulative_return)}|'
                f'{_decimal(metrics.maximum_drawdown)}|'
                f'{_decimal(metrics.turnover_on_initial_capital)}|'
                f'{_decimal(metrics.long_exposure_fraction)}|'
                f'{metrics.marked_session_count}')
        return tuple(lines)


@dataclass(frozen=True)
class ValidationMetricRunReceipt:
    experiment_id: str
    manifest_sha256: str
    folds: tuple[ValidationMetricFoldReceipt, ...]
    benchmark: str = 'buy_and_hold'
    schema_version: int = SCHEMA_VERSION
    status: str = 'synthetic_validation_metrics_only'
    metrics_calculated: bool = True
    comparator_executed: bool = True
    adverse_policy_executed: bool = True
    selection_frozen: bool = False
    holdout_inspected: bool = False
    real_data_validated: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                self.status != 'synthetic_validation_metrics_only' or
                self.benchmark != 'buy_and_hold' or
                tuple(row.fold_id for row in self.folds) != ('fold-1', 'fold-2') or
                self.metrics_calculated is not True or
                self.comparator_executed is not True or
                self.adverse_policy_executed is not True or
                self.selection_frozen is not False or
                self.holdout_inspected is not False or
                self.real_data_validated is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_validation_metric_run_state')

    def canonical_bytes(self) -> bytes:
        lines = (
            f'schema_version={self.schema_version}',
            f'experiment_id={self.experiment_id}',
            f'manifest_sha256={self.manifest_sha256}',
            f'status={self.status}',
            f'benchmark={self.benchmark}',
            *(line for fold in self.folds for line in fold.canonical_lines()),
            'metrics_calculated=true',
            'comparator_executed=true',
            'adverse_policy_executed=true',
            'selection_frozen=false',
            'holdout_inspected=false',
            'real_data_validated=false',
            'investment_performance_established=false',
        )
        return ('\n'.join(lines) + '\n').encode('ascii')

    def output_binding(self, manifest: ExperimentManifest) -> ExperimentOutputReceipt:
        if (not isinstance(manifest, ExperimentManifest) or
                manifest.experiment_id != self.experiment_id or
                manifest.manifest_sha256 != self.manifest_sha256):
            raise ValueError('validation_metric_manifest_mismatch')
        return bind_synthetic_output(manifest, self.canonical_bytes())


def compose_validation_metric_run(
        series: SyntheticSeries, config: ExperimentConfig,
        manifest: ExperimentManifest) -> ValidationMetricRunReceipt:
    """Calculate registered candidate/comparator metrics on validation only."""
    if not isinstance(series, SyntheticSeries) or not isinstance(
            config, ExperimentConfig) or not isinstance(manifest, ExperimentManifest):
        raise ValueError('invalid_validation_metric_input')
    registered_config = ExperimentConfig(adverse_overlap_policy='fifo')
    if config != registered_config:
        raise ValueError('unsupported_validation_metric_configuration')
    expected = register_experiment(
        series, config, experiment_id=manifest.experiment_id,
        code_commit_sha=manifest.code_commit_sha)
    if manifest != expected:
        raise ValueError('validation_metric_manifest_mismatch')

    samples = tuple(
        SampleWindow(session, session, session + config.label_horizon_sessions)
        for session in range(config.sessions))
    policies = (
        ExecutionPolicy(config.base_cost_bps_per_side, config.base_delay_sessions),
        ExecutionPolicy(
            config.adverse_cost_bps_per_side, config.adverse_delay_sessions,
            config.adverse_overlap_policy),
    )
    folds: list[ValidationMetricFoldReceipt] = []
    for index, (start, end) in enumerate(_REGISTERED_WINDOWS, start=1):
        split = plan_fold(samples, FoldSpec(
            0, start, end, config.holdout_start,
            config.training_gap_sessions))
        eligible = set(split.validation_sessions)
        candidate = (TargetState(
            start, _target_at(series, start, config.lookback_sessions)),) + tuple(
                target for target in series.targets
                if target.decision_session > start and
                target.decision_session in eligible)
        comparator = (TargetState(start, Decimal('1')),)
        if (end > config.holdout_start or
                any(row.decision_session not in eligible
                    for row in candidate + comparator)):
            raise ValueError('validation_metric_holdout_boundary_violation')
        bars = series.bars[start:end]
        candidate_base = calculate_evaluation_metrics(
            bars, candidate, initial_cash=config.initial_cash,
            policy=policies[0])
        comparator_base = calculate_evaluation_metrics(
            bars, comparator, initial_cash=config.initial_cash,
            policy=policies[0])
        candidate_adverse = calculate_evaluation_metrics(
            bars, candidate, initial_cash=config.initial_cash,
            policy=policies[1])
        comparator_adverse = calculate_evaluation_metrics(
            bars, comparator, initial_cash=config.initial_cash,
            policy=policies[1])
        folds.append(ValidationMetricFoldReceipt(
            f'fold-{index}', start, end, len(split.validation_sessions),
            candidate_base, comparator_base, candidate_adverse,
            comparator_adverse))

    return ValidationMetricRunReceipt(
        manifest.experiment_id, manifest.manifest_sha256, tuple(folds))
