"""Authorized one-time final holdout inspection for the frozen M3 protocol.

The public receipt binds exact synthetic metric bytes without exposing their
values.  It records engineering readiness only: milestone acceptance, release,
real-data validation, investment performance, merge and trading stay false.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import re

from .evaluation_metrics import EvaluationMetrics, calculate_evaluation_metrics
from .experiment_registry import (
    ExperimentConfig, ExperimentManifest, register_experiment,
)
from .m3_founder_decision import M3FounderDecisionRecord
from .selection_freeze import SelectionFreezeCandidate
from .synthetic_execution import (
    ExecutionPolicy, TargetState, run_long_cash_ledger,
)
from .synthetic_series import SyntheticSeries


SCHEMA_VERSION = 1
INSPECTION_ID = 'm3-final-synthetic-holdout-v1'
_HEX_40 = re.compile(r'[0-9a-f]{40}')
_HEX_64 = re.compile(r'[0-9a-f]{64}')


def _decimal(value: Decimal) -> str:
    return format(value, 'f')


def _target_at(series: SyntheticSeries, session: int, lookback: int) -> Decimal:
    return (Decimal('1') if series.bars[session].close_price >
            series.bars[session - lookback].close_price else Decimal('0'))


@dataclass(frozen=True)
class FinalHoldoutMetrics:
    candidate_base: EvaluationMetrics
    comparator_base: EvaluationMetrics
    candidate_adverse: EvaluationMetrics
    comparator_adverse: EvaluationMetrics

    def __post_init__(self):
        rows = (
            self.candidate_base, self.comparator_base,
            self.candidate_adverse, self.comparator_adverse)
        if any(not isinstance(row, EvaluationMetrics) or
               row.marked_session_count != 40 or
               row.synthetic_only is not True or
               row.holdout_inspected is not False or
               row.investment_performance_established is not False
               for row in rows):
            raise ValueError('invalid_final_holdout_metrics')

    def canonical_bytes(self, *, experiment_id, manifest_sha256,
                        freeze_candidate_sha256, founder_decision_sha256,
                        holdout_start, holdout_end,
                        eligible_decision_count) -> bytes:
        lines = [
            f'schema_version={SCHEMA_VERSION}',
            f'inspection_id={INSPECTION_ID}',
            f'experiment_id={experiment_id}',
            f'manifest_sha256={manifest_sha256}',
            f'freeze_candidate_sha256={freeze_candidate_sha256}',
            f'founder_decision_sha256={founder_decision_sha256}',
            f'holdout={holdout_start}|{holdout_end}|{eligible_decision_count}',
            'benchmark=buy_and_hold',
            'base_policy=10|1|reject',
            'adverse_policy=25|2|fifo',
        ]
        for label, metrics in (
                ('candidate_base', self.candidate_base),
                ('comparator_base', self.comparator_base),
                ('candidate_adverse', self.candidate_adverse),
                ('comparator_adverse', self.comparator_adverse)):
            lines.append(
                f'metrics={label}|'
                f'{_decimal(metrics.gross_cumulative_return)}|'
                f'{_decimal(metrics.net_cumulative_return)}|'
                f'{_decimal(metrics.maximum_drawdown)}|'
                f'{_decimal(metrics.turnover_on_initial_capital)}|'
                f'{_decimal(metrics.long_exposure_fraction)}|'
                f'{metrics.marked_session_count}')
        lines.extend((
            'selection_frozen=true',
            'holdout_inspected=true',
            'synthetic_only=true',
            'real_data_validated=false',
            'investment_performance_established=false',
        ))
        return ('\n'.join(lines) + '\n').encode('ascii')


@dataclass(frozen=True)
class FinalHoldoutReceipt:
    experiment_id: str
    manifest_sha256: str
    freeze_candidate_sha256: str
    founder_decision_sha256: str
    executed_by_code_commit_sha: str
    inspected_at: datetime
    holdout_start: int
    holdout_end: int
    eligible_decision_count: int
    candidate_target_count: int
    candidate_base_fill_count: int
    candidate_adverse_fill_count: int
    comparator_target_count: int
    comparator_base_fill_count: int
    comparator_adverse_fill_count: int
    metric_output_sha256: str
    metric_output_bytes_count: int
    schema_version: int = SCHEMA_VERSION
    inspection_id: str = INSPECTION_ID
    inspection_ordinal: int = 1
    status: str = 'synthetic_holdout_inspected_once'
    scope: str = 'frozen_synthetic_engineering_only'
    benchmark: str = 'buy_and_hold'
    selection_frozen: bool = True
    holdout_authorized: bool = True
    holdout_inspected: bool = True
    metrics_calculated: bool = True
    comparator_executed: bool = True
    adverse_policy_executed: bool = True
    metric_values_redacted: bool = True
    repeat_inspection_authorized: bool = False
    post_holdout_tuning_authorized: bool = False
    m3_engineering_criteria_ready: bool = True
    milestone_acceptance_recorded: bool = False
    release_authorized: bool = False
    real_data_validated: bool = False
    investment_performance_established: bool = False
    merge_authorized: bool = False
    trading_authorized: bool = False

    def __post_init__(self):
        hashes = (
            self.manifest_sha256, self.freeze_candidate_sha256,
            self.founder_decision_sha256, self.metric_output_sha256)
        counts = (
            self.eligible_decision_count, self.candidate_target_count,
            self.candidate_base_fill_count,
            self.candidate_adverse_fill_count,
            self.comparator_target_count, self.comparator_base_fill_count,
            self.comparator_adverse_fill_count,
            self.metric_output_bytes_count)
        if (self.schema_version != SCHEMA_VERSION or
                self.inspection_id != INSPECTION_ID or
                self.inspection_ordinal != 1 or
                self.status != 'synthetic_holdout_inspected_once' or
                self.scope != 'frozen_synthetic_engineering_only' or
                self.benchmark != 'buy_and_hold' or
                not self.experiment_id or
                any(_HEX_64.fullmatch(value or '') is None
                    for value in hashes) or
                _HEX_40.fullmatch(
                    self.executed_by_code_commit_sha or '') is None or
                not isinstance(self.inspected_at, datetime) or
                self.inspected_at.tzinfo is None or
                self.holdout_start != 160 or self.holdout_end != 200 or
                self.eligible_decision_count != 35 or
                any(type(value) is not int or value < 1 for value in counts) or
                self.candidate_base_fill_count > self.candidate_target_count or
                self.candidate_adverse_fill_count > self.candidate_target_count or
                self.comparator_target_count != 1 or
                self.comparator_base_fill_count > self.comparator_target_count or
                self.comparator_adverse_fill_count > self.comparator_target_count or
                any(value is not True for value in (
                    self.selection_frozen, self.holdout_authorized,
                    self.holdout_inspected, self.metrics_calculated,
                    self.comparator_executed, self.adverse_policy_executed,
                    self.metric_values_redacted,
                    self.m3_engineering_criteria_ready)) or
                any(value is not False for value in (
                    self.repeat_inspection_authorized,
                    self.post_holdout_tuning_authorized,
                    self.milestone_acceptance_recorded,
                    self.release_authorized, self.real_data_validated,
                    self.investment_performance_established,
                    self.merge_authorized, self.trading_authorized))):
            raise ValueError('invalid_final_holdout_receipt')

    def public_summary(self) -> dict:
        return {
            'schema_version': self.schema_version,
            'inspection_id': self.inspection_id,
            'inspection_ordinal': self.inspection_ordinal,
            'status': self.status,
            'scope': self.scope,
            'experiment_id': self.experiment_id,
            'manifest_sha256': self.manifest_sha256,
            'freeze_candidate_sha256': self.freeze_candidate_sha256,
            'founder_decision_sha256': self.founder_decision_sha256,
            'executed_by_code_commit_sha': self.executed_by_code_commit_sha,
            'inspected_at': self.inspected_at.isoformat(),
            'holdout_calendar': {
                'start': self.holdout_start,
                'end_exclusive': self.holdout_end,
                'eligible_decision_count': self.eligible_decision_count,
            },
            'benchmark': self.benchmark,
            'execution': {
                'candidate_target_count': self.candidate_target_count,
                'candidate_base_fill_count': self.candidate_base_fill_count,
                'candidate_adverse_fill_count':
                    self.candidate_adverse_fill_count,
                'comparator_target_count': self.comparator_target_count,
                'comparator_base_fill_count':
                    self.comparator_base_fill_count,
                'comparator_adverse_fill_count':
                    self.comparator_adverse_fill_count,
            },
            'metric_output_sha256': self.metric_output_sha256,
            'metric_output_bytes_count': self.metric_output_bytes_count,
            'metric_values_redacted': True,
            'm3_readiness': {
                'ready_count': 6,
                'required_count': 6,
                'next_decision': 'founder_m3_milestone_acceptance',
            },
            'selection_frozen': True,
            'holdout_authorized': True,
            'holdout_inspected': True,
            'metrics_calculated': True,
            'comparator_executed': True,
            'adverse_policy_executed': True,
            'repeat_inspection_authorized': False,
            'post_holdout_tuning_authorized': False,
            'm3_engineering_criteria_ready': True,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'real_data_validated': False,
            'investment_performance_established': False,
            'merge_authorized': False,
            'trading_authorized': False,
            'limitations': [
                'invented deterministic series only',
                'metric values withheld from the public receipt',
                'no repeat inspection or post-holdout tuning authorized',
                'no inference to live markets or investment performance',
            ],
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.public_summary(), sort_keys=True,
            separators=(',', ':')).encode('ascii')

    @property
    def receipt_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True)
class FinalHoldoutInspection:
    receipt: FinalHoldoutReceipt
    metrics: FinalHoldoutMetrics

    def __post_init__(self):
        if (not isinstance(self.receipt, FinalHoldoutReceipt) or
                not isinstance(self.metrics, FinalHoldoutMetrics)):
            raise ValueError('invalid_final_holdout_inspection')
        output = self.metrics.canonical_bytes(
            experiment_id=self.receipt.experiment_id,
            manifest_sha256=self.receipt.manifest_sha256,
            freeze_candidate_sha256=self.receipt.freeze_candidate_sha256,
            founder_decision_sha256=self.receipt.founder_decision_sha256,
            holdout_start=self.receipt.holdout_start,
            holdout_end=self.receipt.holdout_end,
            eligible_decision_count=self.receipt.eligible_decision_count)
        if (sha256(output).hexdigest() != self.receipt.metric_output_sha256 or
                len(output) != self.receipt.metric_output_bytes_count):
            raise ValueError('final_holdout_metric_binding_mismatch')


def inspect_final_synthetic_holdout(
        series, config, manifest, freeze_candidate, founder_decision, *,
        executed_by_code_commit_sha, inspected_at):
    """Inspect the frozen synthetic holdout once without interpreting returns."""
    if (not isinstance(series, SyntheticSeries) or
            not isinstance(config, ExperimentConfig) or
            not isinstance(manifest, ExperimentManifest) or
            not isinstance(freeze_candidate, SelectionFreezeCandidate) or
            not isinstance(founder_decision, M3FounderDecisionRecord)):
        raise ValueError('invalid_final_holdout_input')
    registered_config = ExperimentConfig(adverse_overlap_policy='fifo')
    if config != registered_config:
        raise ValueError('unsupported_final_holdout_configuration')
    expected = register_experiment(
        series, config, experiment_id=manifest.experiment_id,
        code_commit_sha=manifest.code_commit_sha)
    if manifest != expected:
        raise ValueError('final_holdout_manifest_mismatch')
    if (freeze_candidate.experiment_id != manifest.experiment_id or
            freeze_candidate.manifest_sha256 != manifest.manifest_sha256 or
            founder_decision.freeze_candidate_sha256 !=
            freeze_candidate.candidate_sha256 or
            founder_decision.selection_frozen is not True or
            founder_decision.holdout_authorized is not True or
            founder_decision.holdout_inspected is not False):
        raise ValueError('final_holdout_authorization_mismatch')
    if (_HEX_40.fullmatch(executed_by_code_commit_sha or '') is None or
            not isinstance(inspected_at, datetime) or
            inspected_at.tzinfo is None or
            inspected_at <= founder_decision.decided_at):
        raise ValueError('invalid_final_holdout_execution_identity')

    start, end = config.holdout_start, config.sessions
    eligible = tuple(range(start, end - config.label_horizon_sessions))
    candidate: list[TargetState] = []
    previous = None
    for session in eligible:
        target = _target_at(series, session, config.lookback_sessions)
        if target != previous:
            candidate.append(TargetState(session, target))
            previous = target
    candidate_signals = tuple(candidate)
    comparator_signals = (TargetState(start, Decimal('1')),)
    if (not candidate_signals or
            any(row.decision_session not in eligible
                for row in candidate_signals + comparator_signals)):
        raise ValueError('final_holdout_calendar_violation')

    bars = series.bars[start:end]
    base_policy = ExecutionPolicy(
        config.base_cost_bps_per_side, config.base_delay_sessions)
    adverse_policy = ExecutionPolicy(
        config.adverse_cost_bps_per_side, config.adverse_delay_sessions,
        config.adverse_overlap_policy)
    candidate_base_ledger = run_long_cash_ledger(
        bars, candidate_signals, initial_cash=config.initial_cash,
        policy=base_policy)
    candidate_adverse_ledger = run_long_cash_ledger(
        bars, candidate_signals, initial_cash=config.initial_cash,
        policy=adverse_policy)
    comparator_base_ledger = run_long_cash_ledger(
        bars, comparator_signals, initial_cash=config.initial_cash,
        policy=base_policy)
    comparator_adverse_ledger = run_long_cash_ledger(
        bars, comparator_signals, initial_cash=config.initial_cash,
        policy=adverse_policy)
    ledgers = (
        candidate_base_ledger, candidate_adverse_ledger,
        comparator_base_ledger, comparator_adverse_ledger)
    if (any(row.marked_at_session != end - 1 for row in ledgers) or
            any(fill.decision_session not in eligible or
                not start <= fill.execution_session < end
                for row in ledgers for fill in row.fills)):
        raise ValueError('final_holdout_calendar_violation')

    metrics = FinalHoldoutMetrics(
        calculate_evaluation_metrics(
            bars, candidate_signals, initial_cash=config.initial_cash,
            policy=base_policy),
        calculate_evaluation_metrics(
            bars, comparator_signals, initial_cash=config.initial_cash,
            policy=base_policy),
        calculate_evaluation_metrics(
            bars, candidate_signals, initial_cash=config.initial_cash,
            policy=adverse_policy),
        calculate_evaluation_metrics(
            bars, comparator_signals, initial_cash=config.initial_cash,
            policy=adverse_policy),
    )
    metric_output = metrics.canonical_bytes(
        experiment_id=manifest.experiment_id,
        manifest_sha256=manifest.manifest_sha256,
        freeze_candidate_sha256=freeze_candidate.candidate_sha256,
        founder_decision_sha256=founder_decision.decision_sha256,
        holdout_start=start, holdout_end=end,
        eligible_decision_count=len(eligible))
    receipt = FinalHoldoutReceipt(
        experiment_id=manifest.experiment_id,
        manifest_sha256=manifest.manifest_sha256,
        freeze_candidate_sha256=freeze_candidate.candidate_sha256,
        founder_decision_sha256=founder_decision.decision_sha256,
        executed_by_code_commit_sha=executed_by_code_commit_sha,
        inspected_at=inspected_at,
        holdout_start=start,
        holdout_end=end,
        eligible_decision_count=len(eligible),
        candidate_target_count=len(candidate_signals),
        candidate_base_fill_count=len(candidate_base_ledger.fills),
        candidate_adverse_fill_count=len(candidate_adverse_ledger.fills),
        comparator_target_count=len(comparator_signals),
        comparator_base_fill_count=len(comparator_base_ledger.fills),
        comparator_adverse_fill_count=len(comparator_adverse_ledger.fills),
        metric_output_sha256=sha256(metric_output).hexdigest(),
        metric_output_bytes_count=len(metric_output),
    )
    return FinalHoldoutInspection(receipt, metrics)
