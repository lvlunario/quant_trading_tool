from dataclasses import replace
from datetime import datetime, timezone
import json
import unittest

from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.m3_checkpoint import assess_m3_checkpoint
from atlas.m3_milestone_readiness import assess_m3_milestone_readiness
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.selection_freeze import prepare_selection_freeze_candidate
from atlas.synthetic_series import registered_series
from atlas.validation_metric_run import compose_validation_metric_run


class M3CheckpointTests(unittest.TestCase):
    def setUp(self):
        series = registered_series()
        config = replace(ExperimentConfig(), adverse_overlap_policy='fifo')
        manifest = register_experiment(
            series, config, experiment_id='m3-synthetic-metrics-v1',
            code_commit_sha='2dde2f5379c179d267e257581996bcfc542be008')
        metrics = compose_validation_metric_run(series, config, manifest)
        freeze = prepare_selection_freeze_candidate(
            manifest, metrics,
            prepared_by_code_commit_sha=
            'c15f1c6644c0a5d7f4d00f48b7a76389f458da72')
        readiness = assess_m3_milestone_readiness(
            manifest, metrics, freeze,
            assessed_at=datetime(2026, 10, 27, 11, 30,
                                 tzinfo=timezone.utc),
            prepared_by_code_commit_sha='e' * 40)
        self.checkpoint = assess_m3_checkpoint(
            readiness, build_synthetic_options_acceptance_evidence(),
            assessed_at=datetime(2026, 10, 31, 11, 50,
                                 tzinfo=timezone.utc))

    def test_due_checkpoint_keeps_acceptance_blocked(self):
        summary = self.checkpoint.public_summary()
        self.assertEqual((summary['status'], summary['target_status']),
                         ('acceptance_blocked', 'due'))
        self.assertEqual((summary['ready_count'], summary['required_count']),
                         (3, 6))
        self.assertFalse(summary['holdout_inspected'])
        self.assertFalse(summary['milestone_acceptance_recorded'])

    def test_options_engineering_evidence_is_not_founder_acceptance(self):
        summary = self.checkpoint.public_summary()
        self.assertTrue(summary['engineering_evidence'][
            'options_collateral_and_freshness_controls_ready'])
        option_row = summary['criteria'][-1]
        self.assertEqual(option_row, {
            'criterion': 'options_scenario_acceptance',
            'status': 'blocked',
            'blocker': 'founder_scenario_review_required',
        })

    def test_all_three_decisions_remain_explicit(self):
        self.assertEqual(self.checkpoint.public_summary()[
            'decision_dependencies'], [
                'founder_selection_freeze_response',
                'founder_holdout_authorization',
                'founder_options_scenario_review',
            ])

    def test_checkpoint_hash_is_deterministic(self):
        self.assertEqual(self.checkpoint.checkpoint_sha256,
                         self.checkpoint.checkpoint_sha256)
        self.assertEqual(len(self.checkpoint.checkpoint_sha256), 64)

    def test_public_summary_excludes_financial_and_private_values(self):
        payload = json.dumps(self.checkpoint.public_summary())
        for forbidden in ('gross_cumulative_return', 'reserved_cash',
                          'holding', 'account_id', 'source_uri'):
            self.assertNotIn(forbidden, payload)

    def test_controlled_state_cannot_be_promoted(self):
        for change in ({'selection_frozen': True},
                       {'holdout_inspected': True},
                       {'founder_response_recorded': True},
                       {'milestone_accepted': True},
                       {'release_authorized': True},
                       {'real_data_validated': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.checkpoint, **change)

    def test_wrong_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_m3_checkpoint_input'):
            assess_m3_checkpoint(
                object(), build_synthetic_options_acceptance_evidence(),
                assessed_at=self.checkpoint.assessed_at)


if __name__ == '__main__':
    unittest.main()
