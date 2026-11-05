from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.final_holdout import inspect_final_synthetic_holdout
from atlas.m3_founder_decision import record_m3_founder_decisions
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.selection_freeze import SelectionFreezeCandidate
from atlas.synthetic_series import registered_series


class FinalHoldoutTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.series = registered_series()
        self.config = replace(
            ExperimentConfig(), adverse_overlap_policy='fifo')
        manifest_fixture = json.loads((
            fixtures / 'm3-validation-metrics-manifest.json').read_text())
        self.manifest = register_experiment(
            self.series, self.config,
            experiment_id=manifest_fixture['experiment_id'],
            code_commit_sha=manifest_fixture['code_commit_sha'])
        freeze_fixture = json.loads((
            fixtures / 'm3-selection-freeze-candidate.json').read_text())
        freeze_fixture.pop('candidate_sha256')
        self.freeze = SelectionFreezeCandidate(**freeze_fixture)
        self.decision = record_m3_founder_decisions(
            self.freeze, build_synthetic_options_acceptance_evidence(),
            decided_at=datetime(2026, 11, 4, 12, 30,
                                tzinfo=timezone.utc))
        self.inspected_at = datetime(2026, 11, 5, 12, 0,
                                     tzinfo=timezone.utc)

    def inspect(self, **changes):
        inputs = {
            'series': self.series,
            'config': self.config,
            'manifest': self.manifest,
            'freeze_candidate': self.freeze,
            'founder_decision': self.decision,
            'executed_by_code_commit_sha': 'e' * 40,
            'inspected_at': self.inspected_at,
        }
        inputs.update(changes)
        return inspect_final_synthetic_holdout(**inputs)

    def test_inspects_exact_final_calendar_once_after_authorization(self):
        inspection = self.inspect()
        receipt = inspection.receipt
        self.assertEqual(
            (receipt.holdout_start, receipt.holdout_end,
             receipt.eligible_decision_count), (160, 200, 35))
        self.assertEqual(receipt.inspection_ordinal, 1)
        self.assertTrue(receipt.selection_frozen)
        self.assertTrue(receipt.holdout_authorized)
        self.assertTrue(receipt.holdout_inspected)
        self.assertFalse(receipt.repeat_inspection_authorized)
        self.assertFalse(receipt.post_holdout_tuning_authorized)
        for metrics in inspection.metrics.__dict__.values():
            self.assertEqual(metrics.marked_session_count, 40)
            self.assertFalse(metrics.holdout_inspected)
            self.assertFalse(metrics.investment_performance_established)

    def test_public_receipt_is_redacted_but_binds_exact_metric_bytes(self):
        receipt = self.inspect().receipt
        summary = receipt.public_summary()
        payload = json.dumps(summary).lower()
        self.assertEqual(summary['m3_readiness'], {
            'ready_count': 6,
            'required_count': 6,
            'next_decision': 'founder_m3_milestone_acceptance',
        })
        self.assertEqual(len(receipt.metric_output_sha256), 64)
        self.assertEqual(len(receipt.receipt_sha256), 64)
        self.assertGreater(receipt.metric_output_bytes_count, 0)
        for forbidden in (
                'gross_cumulative_return', 'net_cumulative_return',
                'maximum_drawdown', 'turnover_on_initial_capital',
                'long_exposure_fraction', 'open_price', 'close_price',
                'cash_after', 'shares_after', 'traded_notional'):
            self.assertNotIn(forbidden, payload)

    def test_deterministic_reproduction_cannot_create_an_alternative_result(self):
        first = self.inspect()
        second = self.inspect()
        self.assertEqual(first, second)
        self.assertEqual(first.receipt.metric_output_sha256,
                         second.receipt.metric_output_sha256)
        changed_identity = self.inspect(executed_by_code_commit_sha='f' * 40)
        self.assertEqual(first.receipt.metric_output_sha256,
                         changed_identity.receipt.metric_output_sha256)
        self.assertNotEqual(first.receipt.receipt_sha256,
                            changed_identity.receipt.receipt_sha256)

    def test_configuration_manifest_and_freeze_changes_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'unsupported_final_holdout_configuration'):
            self.inspect(config=ExperimentConfig())
        with self.assertRaisesRegex(
                ValueError, 'final_holdout_manifest_mismatch'):
            self.inspect(manifest=replace(
                self.manifest, config_sha256='a' * 64))
        changed_freeze = replace(
            self.freeze, validation_output_sha256='b' * 64)
        with self.assertRaisesRegex(
                ValueError, 'final_holdout_authorization_mismatch'):
            self.inspect(freeze_candidate=changed_freeze)

    def test_execution_must_follow_the_actual_founder_decision(self):
        with self.assertRaisesRegex(
                ValueError, 'invalid_final_holdout_execution_identity'):
            self.inspect(inspected_at=datetime(2026, 11, 5, 12, 0))
        with self.assertRaisesRegex(
                ValueError, 'invalid_final_holdout_execution_identity'):
            self.inspect(inspected_at=self.decision.decided_at)
        with self.assertRaisesRegex(
                ValueError, 'invalid_final_holdout_execution_identity'):
            self.inspect(executed_by_code_commit_sha='not-a-commit')

    def test_checked_in_receipt_matches_the_single_registered_inspection(self):
        checked_in = json.loads((
            Path(__file__).parents[1] / 'fixtures' /
            'm3-final-holdout-receipt.json').read_text())
        inspection = self.inspect(
            executed_by_code_commit_sha=
                checked_in['executed_by_code_commit_sha'],
            inspected_at=datetime.fromisoformat(checked_in['inspected_at']))
        expected = inspection.receipt.public_summary()
        expected['receipt_sha256'] = inspection.receipt.receipt_sha256
        self.assertEqual(checked_in, expected)

    def test_adjacent_authority_cannot_be_promoted(self):
        receipt = self.inspect().receipt
        for change in (
                {'inspection_ordinal': 2},
                {'repeat_inspection_authorized': True},
                {'post_holdout_tuning_authorized': True},
                {'milestone_acceptance_recorded': True},
                {'release_authorized': True},
                {'real_data_validated': True},
                {'investment_performance_established': True},
                {'merge_authorized': True},
                {'trading_authorized': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(receipt, **change)


if __name__ == '__main__':
    unittest.main()
