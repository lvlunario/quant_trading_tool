from dataclasses import replace
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import unittest

from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.m3_milestone_readiness import assess_m3_milestone_readiness
from atlas.selection_freeze import prepare_selection_freeze_candidate
from atlas.synthetic_series import registered_series
from atlas.validation_metric_run import compose_validation_metric_run


class M3MilestoneReadinessTests(unittest.TestCase):
    def setUp(self):
        self.series = registered_series()
        self.config = replace(
            ExperimentConfig(), adverse_overlap_policy='fifo')
        self.manifest = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-metrics-v1',
            code_commit_sha='2dde2f5379c179d267e257581996bcfc542be008')
        self.metrics = compose_validation_metric_run(
            self.series, self.config, self.manifest)
        self.freeze = prepare_selection_freeze_candidate(
            self.manifest, self.metrics,
            prepared_by_code_commit_sha=
            'c15f1c6644c0a5d7f4d00f48b7a76389f458da72')
        self.assessed_at = datetime(
            2026, 10, 27, 19, 30,
            tzinfo=timezone.utc).astimezone(timezone.utc)
        self.readiness = assess_m3_milestone_readiness(
            self.manifest, self.metrics, self.freeze,
            assessed_at=self.assessed_at,
            prepared_by_code_commit_sha='e' * 40)

    def test_summary_separates_ready_controls_from_closed_gates(self):
        summary = self.readiness.public_summary()
        self.assertEqual((summary['status'], summary['scope']),
                         ('blocked', 'synthetic_engineering_only'))
        self.assertEqual((summary['ready_count'], summary['required_count']),
                         (3, 6))
        self.assertEqual(
            [row['status'] for row in summary['criteria']],
            ['ready', 'ready', 'ready', 'blocked', 'blocked', 'blocked'])
        self.assertFalse(summary['founder_response_recorded'])
        self.assertFalse(summary['milestone_acceptance_recorded'])
        self.assertFalse(summary['release_authorized'])

    def test_readiness_binds_exact_validation_and_freeze_candidate(self):
        binding = self.metrics.output_binding(self.manifest)
        self.assertEqual(self.readiness.manifest_sha256,
                         self.manifest.manifest_sha256)
        self.assertEqual(self.readiness.validation_output_sha256,
                         binding.output_sha256)
        self.assertEqual(self.readiness.validation_output_bytes_count,
                         binding.output_bytes_count)
        self.assertEqual(self.readiness.freeze_candidate_sha256,
                         self.freeze.candidate_sha256)
        self.assertEqual(self.readiness.readiness_sha256,
                         sha256(self.readiness.canonical_bytes()).hexdigest())

    def test_decision_and_engineering_dependencies_are_distinct(self):
        summary = self.readiness.public_summary()
        self.assertEqual(summary['decision_dependencies'], [
            'founder_selection_freeze_response',
            'founder_holdout_authorization',
        ])
        self.assertEqual(summary['engineering_dependencies'], [
            'final_holdout_receipt',
            'options_collateral_reservation_evidence',
            'stale_chain_blocking_evidence',
        ])

    def test_manila_date_controls_target_status(self):
        cases = (
            ('2026-10-30T15:59:59+00:00', 'scheduled', 1),
            ('2026-10-30T16:00:00+00:00', 'due', 0),
            ('2026-10-31T15:59:59+00:00', 'due', 0),
            ('2026-10-31T16:00:00+00:00', 'elapsed', -1),
        )
        for timestamp, status, days in cases:
            with self.subTest(timestamp=timestamp):
                readiness = replace(
                    self.readiness,
                    assessed_at=datetime.fromisoformat(timestamp))
                summary = readiness.public_summary()
                self.assertEqual((summary['target_status'],
                                  summary['days_to_target']), (status, days))

    def test_mismatched_evidence_fails_closed(self):
        changed = replace(
            self.freeze, validation_output_sha256='f' * 64)
        with self.assertRaisesRegex(
                ValueError, 'invalid_m3_milestone_readiness_input'):
            assess_m3_milestone_readiness(
                self.manifest, self.metrics, changed,
                assessed_at=self.assessed_at,
                prepared_by_code_commit_sha='e' * 40)

    def test_controlled_state_cannot_be_promoted(self):
        for change in (
                {'selection_frozen': True}, {'holdout_authorized': True},
                {'holdout_inspected': True},
                {'options_acceptance_ready': True},
                {'real_data_validated': True},
                {'founder_response_recorded': True},
                {'milestone_accepted': True},
                {'release_authorized': True},
                {'investment_performance_established': True},
                {'registered_protocol_ready': False},
                {'target_date': date(2026, 11, 1)}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.readiness, **change)

    def test_public_summary_excludes_sensitive_or_metric_values(self):
        encoded = json.dumps(self.readiness.public_summary())
        for excluded in (
                'metric_value', 'gross_cumulative_return',
                'net_cumulative_return', 'account_id', 'holding',
                'source_uri', 'approval_id'):
            self.assertNotIn(excluded, encoded)


if __name__ == '__main__':
    unittest.main()
