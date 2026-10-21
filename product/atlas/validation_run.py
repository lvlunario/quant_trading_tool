"""Validation-only composition for the registered synthetic M3 experiment.

This module connects the frozen invented series, chronological split planner
and execution ledger. Its public receipts contain structural counts and identity
hashes only. They do not expose ledger values, calculate performance, run the
comparator or inspect the reserved holdout.
"""
from dataclasses import dataclass
from decimal import Decimal

from .evaluation import FoldSpec, SampleWindow, plan_fold
from .experiment_registry import (
    ExperimentConfig, ExperimentManifest, ExperimentOutputReceipt,
    bind_synthetic_output, register_experiment,
)
from .synthetic_execution import ExecutionPolicy, TargetState, run_long_cash_ledger
from .synthetic_series import SyntheticSeries


SCHEMA_VERSION = 1
_REGISTERED_WINDOWS = ((80, 120), (120, 160))
_ADVERSE_BLOCKER = 'overlapping_execution_policy_undefined'


@dataclass(frozen=True)
class ValidationFoldReceipt:
    fold_id: str
    validation_start: int
    validation_end: int
    train_count: int
    validation_count: int
    purged_count: int
    excluded_count: int
    target_count: int
    fill_count: int

    def __post_init__(self):
        counts = (
            self.train_count, self.validation_count, self.purged_count,
            self.excluded_count, self.target_count, self.fill_count)
        if (self.fold_id not in ('fold-1', 'fold-2') or
                type(self.validation_start) is not int or
                type(self.validation_end) is not int or
                self.validation_start >= self.validation_end or
                any(type(value) is not int or value < 0 for value in counts) or
                self.fill_count > self.target_count):
            raise ValueError('invalid_validation_fold_receipt')


@dataclass(frozen=True)
class ValidationRunReceipt:
    experiment_id: str
    manifest_sha256: str
    folds: tuple[ValidationFoldReceipt, ...]
    base_cost_bps_per_side: int
    base_delay_sessions: int
    schema_version: int = SCHEMA_VERSION
    status: str = 'synthetic_plumbing_only'
    comparator_executed: bool = False
    adverse_policy_executed: bool = False
    adverse_blocker: str = _ADVERSE_BLOCKER
    metrics_calculated: bool = False
    holdout_inspected: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                self.status != 'synthetic_plumbing_only' or
                tuple(row.fold_id for row in self.folds) != ('fold-1', 'fold-2') or
                self.comparator_executed is not False or
                self.adverse_policy_executed is not False or
                self.adverse_blocker != _ADVERSE_BLOCKER or
                self.metrics_calculated is not False or
                self.holdout_inspected is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_validation_run_state')

    def canonical_bytes(self) -> bytes:
        lines = (
            f'schema_version={self.schema_version}',
            f'experiment_id={self.experiment_id}',
            f'manifest_sha256={self.manifest_sha256}',
            f'status={self.status}',
            f'base_policy={self.base_cost_bps_per_side}|{self.base_delay_sessions}',
            *(f'fold={row.fold_id}|{row.validation_start}|{row.validation_end}|'
              f'{row.train_count}|{row.validation_count}|{row.purged_count}|'
              f'{row.excluded_count}|{row.target_count}|{row.fill_count}'
              for row in self.folds),
            'comparator_executed=false',
            'adverse_policy_executed=false',
            f'adverse_blocker={self.adverse_blocker}',
            'metrics_calculated=false',
            'holdout_inspected=false',
            'investment_performance_established=false',
        )
        return ('\n'.join(lines) + '\n').encode('ascii')

    def output_binding(self, manifest: ExperimentManifest) -> ExperimentOutputReceipt:
        if (not isinstance(manifest, ExperimentManifest) or
                manifest.experiment_id != self.experiment_id or
                manifest.manifest_sha256 != self.manifest_sha256):
            raise ValueError('validation_manifest_mismatch')
        return bind_synthetic_output(manifest, self.canonical_bytes())


@dataclass(frozen=True)
class AdverseValidationRunReceipt:
    experiment_id: str
    manifest_sha256: str
    folds: tuple[ValidationFoldReceipt, ...]
    adverse_cost_bps_per_side: int
    adverse_delay_sessions: int
    adverse_overlap_policy: str
    schema_version: int = SCHEMA_VERSION
    status: str = 'synthetic_plumbing_only'
    comparator_executed: bool = False
    adverse_policy_executed: bool = True
    metrics_calculated: bool = False
    holdout_inspected: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                self.status != 'synthetic_plumbing_only' or
                tuple(row.fold_id for row in self.folds) != ('fold-1', 'fold-2') or
                self.adverse_cost_bps_per_side != 25 or
                self.adverse_delay_sessions != 2 or
                self.adverse_overlap_policy != 'fifo' or
                self.comparator_executed is not False or
                self.adverse_policy_executed is not True or
                self.metrics_calculated is not False or
                self.holdout_inspected is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_adverse_validation_run_state')

    def canonical_bytes(self) -> bytes:
        lines = (
            f'schema_version={self.schema_version}',
            f'experiment_id={self.experiment_id}',
            f'manifest_sha256={self.manifest_sha256}',
            f'status={self.status}',
            f'adverse_policy={self.adverse_cost_bps_per_side}|'
            f'{self.adverse_delay_sessions}|{self.adverse_overlap_policy}',
            *(f'fold={row.fold_id}|{row.validation_start}|{row.validation_end}|'
              f'{row.train_count}|{row.validation_count}|{row.purged_count}|'
              f'{row.excluded_count}|{row.target_count}|{row.fill_count}'
              for row in self.folds),
            'comparator_executed=false',
            'adverse_policy_executed=true',
            'metrics_calculated=false',
            'holdout_inspected=false',
            'investment_performance_established=false',
        )
        return ('\n'.join(lines) + '\n').encode('ascii')

    def output_binding(self, manifest: ExperimentManifest) -> ExperimentOutputReceipt:
        if (not isinstance(manifest, ExperimentManifest) or
                manifest.experiment_id != self.experiment_id or
                manifest.manifest_sha256 != self.manifest_sha256):
            raise ValueError('adverse_validation_manifest_mismatch')
        return bind_synthetic_output(manifest, self.canonical_bytes())


def _target_at(series: SyntheticSeries, session: int, lookback: int) -> Decimal:
    return (Decimal('1') if series.bars[session].close_price >
            series.bars[session - lookback].close_price else Decimal('0'))


def compose_validation_run(
        series: SyntheticSeries, config: ExperimentConfig,
        manifest: ExperimentManifest) -> ValidationRunReceipt:
    """Run only registered validation windows through the base ledger.

    The exact manifest is reproduced before execution.  Bars in [160, 200)
    never enter a split ledger; validation-boundary rows may be present only as
    marking/execution events and never as eligible decisions.
    """
    if not isinstance(series, SyntheticSeries) or not isinstance(
            config, ExperimentConfig) or not isinstance(manifest, ExperimentManifest):
        raise ValueError('invalid_validation_input')
    if config != ExperimentConfig():
        raise ValueError('unsupported_validation_protocol_configuration')
    expected = register_experiment(
        series, config, experiment_id=manifest.experiment_id,
        code_commit_sha=manifest.code_commit_sha)
    if manifest != expected:
        raise ValueError('validation_manifest_mismatch')

    samples = tuple(
        SampleWindow(session, session, session + config.label_horizon_sessions)
        for session in range(config.sessions))
    base_policy = ExecutionPolicy(
        config.base_cost_bps_per_side, config.base_delay_sessions)
    fold_receipts: list[ValidationFoldReceipt] = []
    for index, (start, end) in enumerate(_REGISTERED_WINDOWS, start=1):
        split = plan_fold(samples, FoldSpec(
            0, start, end, config.holdout_start,
            config.training_gap_sessions))
        eligible = set(split.validation_sessions)
        signals = (TargetState(
            start, _target_at(series, start, config.lookback_sessions)),) + tuple(
                target for target in series.targets
                if target.decision_session > start and
                target.decision_session in eligible)
        ledger = run_long_cash_ledger(
            series.bars[start:end], signals, initial_cash=config.initial_cash,
            policy=base_policy)
        if (ledger.marked_at_session >= config.holdout_start or
                any(fill.decision_session not in eligible or
                    fill.execution_session >= config.holdout_start
                    for fill in ledger.fills)):
            raise ValueError('holdout_boundary_violation')
        fold_receipts.append(ValidationFoldReceipt(
            f'fold-{index}', start, end, len(split.train_sessions),
            len(split.validation_sessions), len(split.purged_sessions),
            len(split.excluded_sessions), len(signals), len(ledger.fills)))

    return ValidationRunReceipt(
        manifest.experiment_id, manifest.manifest_sha256,
        tuple(fold_receipts), config.base_cost_bps_per_side,
        config.base_delay_sessions)


def compose_adverse_validation_run(
        series: SyntheticSeries, config: ExperimentConfig,
        manifest: ExperimentManifest) -> AdverseValidationRunReceipt:
    """Run the registered validation windows through the amended adverse ledger."""
    if not isinstance(series, SyntheticSeries) or not isinstance(
            config, ExperimentConfig) or not isinstance(manifest, ExperimentManifest):
        raise ValueError('invalid_adverse_validation_input')
    registered_config = ExperimentConfig(adverse_overlap_policy='fifo')
    if config != registered_config:
        raise ValueError('unsupported_adverse_validation_configuration')
    expected = register_experiment(
        series, config, experiment_id=manifest.experiment_id,
        code_commit_sha=manifest.code_commit_sha)
    if manifest != expected:
        raise ValueError('adverse_validation_manifest_mismatch')

    samples = tuple(
        SampleWindow(session, session, session + config.label_horizon_sessions)
        for session in range(config.sessions))
    adverse_policy = ExecutionPolicy(
        config.adverse_cost_bps_per_side, config.adverse_delay_sessions,
        config.adverse_overlap_policy)
    fold_receipts: list[ValidationFoldReceipt] = []
    for index, (start, end) in enumerate(_REGISTERED_WINDOWS, start=1):
        split = plan_fold(samples, FoldSpec(
            0, start, end, config.holdout_start,
            config.training_gap_sessions))
        eligible = set(split.validation_sessions)
        signals = (TargetState(
            start, _target_at(series, start, config.lookback_sessions)),) + tuple(
                target for target in series.targets
                if target.decision_session > start and
                target.decision_session in eligible)
        ledger = run_long_cash_ledger(
            series.bars[start:end], signals, initial_cash=config.initial_cash,
            policy=adverse_policy)
        if (ledger.marked_at_session >= config.holdout_start or
                any(fill.decision_session not in eligible or
                    fill.execution_session >= config.holdout_start
                    for fill in ledger.fills)):
            raise ValueError('holdout_boundary_violation')
        fold_receipts.append(ValidationFoldReceipt(
            f'fold-{index}', start, end, len(split.train_sessions),
            len(split.validation_sessions), len(split.purged_sessions),
            len(split.excluded_sessions), len(signals), len(ledger.fills)))

    return AdverseValidationRunReceipt(
        manifest.experiment_id, manifest.manifest_sha256,
        tuple(fold_receipts), config.adverse_cost_bps_per_side,
        config.adverse_delay_sessions, config.adverse_overlap_policy)
