"""Fail-closed M3 milestone readiness from synthetic experiment evidence.

The snapshot separates completed engineering controls from decisions and
evidence that do not exist. It cannot freeze selection, inspect a holdout,
record founder acceptance or establish investment performance.
"""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import re
from zoneinfo import ZoneInfo

from .experiment_registry import ExperimentManifest
from .selection_freeze import (
    SelectionFreezeCandidate, prepare_selection_freeze_candidate,
)
from .validation_metric_run import ValidationMetricRunReceipt


SCHEMA_VERSION = 1
M3_TARGET_DATE = date(2026, 10, 31)
_HEX_40 = re.compile(r'[0-9a-f]{40}')
_HEX_64 = re.compile(r'[0-9a-f]{64}')


@dataclass(frozen=True)
class M3MilestoneReadiness:
    assessed_at: datetime
    experiment_id: str
    manifest_sha256: str
    validation_output_sha256: str
    validation_output_bytes_count: int
    freeze_candidate_sha256: str
    prepared_by_code_commit_sha: str
    target_date: date = M3_TARGET_DATE
    schema_version: int = SCHEMA_VERSION
    scope: str = 'synthetic_engineering_only'
    registered_protocol_ready: bool = True
    reproducible_validation_ready: bool = True
    costs_and_benchmark_ready: bool = True
    selection_frozen: bool = False
    holdout_authorized: bool = False
    holdout_inspected: bool = False
    options_acceptance_ready: bool = False
    real_data_validated: bool = False
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    release_authorized: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.target_date != M3_TARGET_DATE or
                not self.experiment_id or
                _HEX_64.fullmatch(self.manifest_sha256) is None or
                _HEX_64.fullmatch(self.validation_output_sha256) is None or
                type(self.validation_output_bytes_count) is not int or
                self.validation_output_bytes_count < 1 or
                _HEX_64.fullmatch(self.freeze_candidate_sha256) is None or
                _HEX_40.fullmatch(self.prepared_by_code_commit_sha) is None or
                self.scope != 'synthetic_engineering_only' or
                self.registered_protocol_ready is not True or
                self.reproducible_validation_ready is not True or
                self.costs_and_benchmark_ready is not True or
                self.selection_frozen is not False or
                self.holdout_authorized is not False or
                self.holdout_inspected is not False or
                self.options_acceptance_ready is not False or
                self.real_data_validated is not False or
                self.founder_response_recorded is not False or
                self.milestone_accepted is not False or
                self.release_authorized is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_m3_milestone_readiness')

    def canonical_bytes(self) -> bytes:
        lines = (
            f'schema_version={self.schema_version}',
            f'assessed_at={self.assessed_at.isoformat()}',
            f'target_date={self.target_date.isoformat()}',
            f'experiment_id={self.experiment_id}',
            f'manifest_sha256={self.manifest_sha256}',
            f'validation_output_sha256={self.validation_output_sha256}',
            f'validation_output_bytes_count={self.validation_output_bytes_count}',
            f'freeze_candidate_sha256={self.freeze_candidate_sha256}',
            f'prepared_by_code_commit_sha={self.prepared_by_code_commit_sha}',
            f'scope={self.scope}',
            'registered_protocol_ready=true',
            'reproducible_validation_ready=true',
            'costs_and_benchmark_ready=true',
            'selection_frozen=false',
            'holdout_authorized=false',
            'holdout_inspected=false',
            'options_acceptance_ready=false',
            'real_data_validated=false',
            'founder_response_recorded=false',
            'milestone_accepted=false',
            'release_authorized=false',
            'investment_performance_established=false',
        )
        return ('\n'.join(lines) + '\n').encode('ascii')

    @property
    def readiness_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

    def public_summary(self) -> dict:
        local_date = self.assessed_at.astimezone(
            ZoneInfo('Asia/Manila')).date()
        days_to_target = (self.target_date - local_date).days
        if days_to_target > 0:
            target_status = 'scheduled'
        elif days_to_target == 0:
            target_status = 'due'
        else:
            target_status = 'elapsed'
        criteria = (
            ('registered_protocol', True, 'none'),
            ('reproducible_validation', True, 'none'),
            ('costs_and_benchmark', True, 'none'),
            ('selection_freeze', False,
             'founder_selection_freeze_response_required'),
            ('final_holdout', False,
             'selection_freeze_and_holdout_authorization_required'),
            ('options_scenario_acceptance', False,
             'collateral_and_stale_chain_evidence_incomplete'),
        )
        return {
            'schema_version': self.schema_version,
            'status': 'blocked',
            'phase': 'M3 Strategy laboratory',
            'scope': self.scope,
            'assessed_at': self.assessed_at.isoformat(),
            'target_date': self.target_date.isoformat(),
            'target_status': target_status,
            'days_to_target': days_to_target,
            'criteria': [
                {
                    'criterion': name,
                    'status': 'ready' if ready else 'blocked',
                    'blocker': blocker,
                }
                for name, ready, blocker in criteria
            ],
            'ready_count': sum(ready for _, ready, _ in criteria),
            'required_count': len(criteria),
            'decision_dependencies': [
                'founder_selection_freeze_response',
                'founder_holdout_authorization',
            ],
            'engineering_dependencies': [
                'final_holdout_receipt',
                'options_collateral_reservation_evidence',
                'stale_chain_blocking_evidence',
            ],
            'real_data_validated': False,
            'founder_response_recorded': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'investment_performance_established': False,
            'recommendation': (
                'keep holdout sealed; request explicit selection and holdout '
                'decisions; complete options evidence before M3 acceptance'),
        }


def assess_m3_milestone_readiness(
        manifest: ExperimentManifest, metrics: ValidationMetricRunReceipt,
        freeze_candidate: SelectionFreezeCandidate, *, assessed_at: datetime,
        prepared_by_code_commit_sha: str) -> M3MilestoneReadiness:
    """Compose exact registered evidence without promoting controlled state."""
    if (not isinstance(manifest, ExperimentManifest) or
            not isinstance(metrics, ValidationMetricRunReceipt) or
            not isinstance(freeze_candidate, SelectionFreezeCandidate)):
        raise ValueError('invalid_m3_milestone_readiness_input')
    expected = prepare_selection_freeze_candidate(
        manifest, metrics,
        prepared_by_code_commit_sha=
        freeze_candidate.prepared_by_code_commit_sha)
    if freeze_candidate != expected:
        raise ValueError('invalid_m3_milestone_readiness_input')
    binding = metrics.output_binding(manifest)
    return M3MilestoneReadiness(
        assessed_at=assessed_at,
        experiment_id=manifest.experiment_id,
        manifest_sha256=manifest.manifest_sha256,
        validation_output_sha256=binding.output_sha256,
        validation_output_bytes_count=binding.output_bytes_count,
        freeze_candidate_sha256=freeze_candidate.candidate_sha256,
        prepared_by_code_commit_sha=prepared_by_code_commit_sha,
    )
