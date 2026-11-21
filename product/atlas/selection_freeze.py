"""Prospective M3 selection-freeze decision candidate.

This module binds the exact synthetic validation receipt to a recommended
disposition without recording a founder response or authorizing holdout use.
The candidate is governance evidence, not an investment-performance result.
"""
from dataclasses import dataclass
from hashlib import sha256
import re

from .experiment_registry import ExperimentManifest
from .validation_metric_run import ValidationMetricRunReceipt


SCHEMA_VERSION = 1
_HEX_40 = re.compile(r'[0-9a-f]{40}')
_HEX_64 = re.compile(r'[0-9a-f]{64}')


@dataclass(frozen=True)
class SelectionFreezeCandidate:
    experiment_id: str
    manifest_sha256: str
    validation_output_sha256: str
    validation_output_bytes_count: int
    prepared_by_code_commit_sha: str
    schema_version: int = SCHEMA_VERSION
    status: str = 'review_required'
    recommended_disposition: str = 'freeze_without_tuning'
    candidate_changed_after_validation: bool = False
    metric_definition_changed_after_validation: bool = False
    selection_frozen: bool = False
    holdout_authorized: bool = False
    founder_response_recorded: bool = False
    holdout_inspected: bool = False
    real_data_validated: bool = False
    milestone_accepted: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                not self.experiment_id or
                _HEX_64.fullmatch(self.manifest_sha256) is None or
                _HEX_64.fullmatch(self.validation_output_sha256) is None or
                type(self.validation_output_bytes_count) is not int or
                self.validation_output_bytes_count < 1 or
                _HEX_40.fullmatch(self.prepared_by_code_commit_sha) is None or
                self.status != 'review_required' or
                self.recommended_disposition != 'freeze_without_tuning' or
                self.candidate_changed_after_validation is not False or
                self.metric_definition_changed_after_validation is not False or
                self.selection_frozen is not False or
                self.holdout_authorized is not False or
                self.founder_response_recorded is not False or
                self.holdout_inspected is not False or
                self.real_data_validated is not False or
                self.milestone_accepted is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_selection_freeze_candidate')

    def canonical_bytes(self) -> bytes:
        lines = (
            f'schema_version={self.schema_version}',
            f'experiment_id={self.experiment_id}',
            f'manifest_sha256={self.manifest_sha256}',
            f'validation_output_sha256={self.validation_output_sha256}',
            f'validation_output_bytes_count={self.validation_output_bytes_count}',
            f'prepared_by_code_commit_sha={self.prepared_by_code_commit_sha}',
            f'status={self.status}',
            f'recommended_disposition={self.recommended_disposition}',
            'candidate_changed_after_validation=false',
            'metric_definition_changed_after_validation=false',
            'selection_frozen=false',
            'holdout_authorized=false',
            'founder_response_recorded=false',
            'holdout_inspected=false',
            'real_data_validated=false',
            'milestone_accepted=false',
            'investment_performance_established=false',
        )
        return ('\n'.join(lines) + '\n').encode('ascii')

    @property
    def candidate_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


def prepare_selection_freeze_candidate(
        manifest: ExperimentManifest, metrics: ValidationMetricRunReceipt,
        *, prepared_by_code_commit_sha: str) -> SelectionFreezeCandidate:
    """Recommend a freeze while leaving every controlled gate closed."""
    if (not isinstance(manifest, ExperimentManifest) or
            not isinstance(metrics, ValidationMetricRunReceipt)):
        raise ValueError('invalid_selection_freeze_input')
    binding = metrics.output_binding(manifest)
    return SelectionFreezeCandidate(
        experiment_id=manifest.experiment_id,
        manifest_sha256=manifest.manifest_sha256,
        validation_output_sha256=binding.output_sha256,
        validation_output_bytes_count=binding.output_bytes_count,
        prepared_by_code_commit_sha=prepared_by_code_commit_sha,
    )
