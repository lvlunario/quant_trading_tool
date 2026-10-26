from dataclasses import replace
from hashlib import sha256
import unittest

from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.selection_freeze import (
    SelectionFreezeCandidate, prepare_selection_freeze_candidate,
)
from atlas.synthetic_series import registered_series
from atlas.validation_metric_run import compose_validation_metric_run


class SelectionFreezeTests(unittest.TestCase):
    def setUp(self):
        self.series = registered_series()
        self.config = replace(
            ExperimentConfig(), adverse_overlap_policy='fifo')
        self.manifest = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-metrics-v1',
            code_commit_sha='d' * 40)
        self.metrics = compose_validation_metric_run(
            self.series, self.config, self.manifest)

    def candidate(self):
        return prepare_selection_freeze_candidate(
            self.manifest, self.metrics,
            prepared_by_code_commit_sha='e' * 40)

    def test_candidate_binds_exact_registered_validation_output(self):
        candidate = self.candidate()
        binding = self.metrics.output_binding(self.manifest)
        self.assertEqual(candidate.experiment_id, self.manifest.experiment_id)
        self.assertEqual(candidate.manifest_sha256,
                         self.manifest.manifest_sha256)
        self.assertEqual(candidate.validation_output_sha256,
                         binding.output_sha256)
        self.assertEqual(candidate.validation_output_bytes_count,
                         binding.output_bytes_count)
        self.assertEqual(candidate.status, 'review_required')
        self.assertEqual(candidate.recommended_disposition,
                         'freeze_without_tuning')

    def test_candidate_has_independent_canonical_hash(self):
        candidate = self.candidate()
        expected = (
            'schema_version=1\n'
            'experiment_id=m3-synthetic-metrics-v1\n'
            f'manifest_sha256={self.manifest.manifest_sha256}\n'
            f'validation_output_sha256='
            f'{self.metrics.output_binding(self.manifest).output_sha256}\n'
            f'validation_output_bytes_count='
            f'{self.metrics.output_binding(self.manifest).output_bytes_count}\n'
            f'prepared_by_code_commit_sha={'e' * 40}\n'
            'status=review_required\n'
            'recommended_disposition=freeze_without_tuning\n'
            'candidate_changed_after_validation=false\n'
            'metric_definition_changed_after_validation=false\n'
            'selection_frozen=false\n'
            'holdout_authorized=false\n'
            'founder_response_recorded=false\n'
            'holdout_inspected=false\n'
            'real_data_validated=false\n'
            'milestone_accepted=false\n'
            'investment_performance_established=false\n').encode('ascii')
        self.assertEqual(candidate.canonical_bytes(), expected)
        self.assertEqual(candidate.candidate_sha256,
                         sha256(expected).hexdigest())

    def test_manifest_mismatch_fails_closed(self):
        other = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-metrics-v2',
            code_commit_sha='d' * 40)
        with self.assertRaisesRegex(
                ValueError, 'validation_metric_manifest_mismatch'):
            prepare_selection_freeze_candidate(
                other, self.metrics, prepared_by_code_commit_sha='e' * 40)

    def test_candidate_cannot_record_response_or_open_controlled_gates(self):
        candidate = self.candidate()
        for change in (
                {'selection_frozen': True}, {'holdout_authorized': True},
                {'founder_response_recorded': True},
                {'holdout_inspected': True}, {'real_data_validated': True},
                {'milestone_accepted': True},
                {'investment_performance_established': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(candidate, **change)

    def test_candidate_cannot_hide_post_validation_changes(self):
        candidate = self.candidate()
        for change in (
                {'candidate_changed_after_validation': True},
                {'metric_definition_changed_after_validation': True},
                {'recommended_disposition': 'tune_and_retry'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(candidate, **change)

    def test_invalid_identity_fields_fail_closed(self):
        candidate = self.candidate()
        for change in (
                {'manifest_sha256': '0' * 63},
                {'validation_output_sha256': 'g' * 64},
                {'validation_output_bytes_count': 0},
                {'prepared_by_code_commit_sha': 'e' * 39},
                {'status': 'approved'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                SelectionFreezeCandidate(**{**candidate.__dict__, **change})


if __name__ == '__main__':
    unittest.main()
