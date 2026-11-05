from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import unittest

from atlas.evaluation_metrics import EvaluationMetrics
from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.synthetic_series import registered_series
from atlas.validation_metric_run import (
    ValidationMetricFoldReceipt, ValidationMetricRunReceipt,
    compose_validation_metric_run,
)


class ValidationMetricRunTests(unittest.TestCase):
    def setUp(self):
        self.series = registered_series()
        self.config = replace(
            ExperimentConfig(), adverse_overlap_policy='fifo')
        self.manifest = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-metrics-v1',
            code_commit_sha='d' * 40)

    def test_registered_run_contains_two_aligned_validation_folds(self):
        receipt = compose_validation_metric_run(
            self.series, self.config, self.manifest)
        self.assertEqual(
            tuple((row.fold_id, row.validation_start, row.validation_end,
                   row.eligible_decision_count) for row in receipt.folds),
            (('fold-1', 80, 120, 35), ('fold-2', 120, 160, 35)))
        for fold in receipt.folds:
            for metrics in (
                    fold.candidate_base, fold.comparator_base,
                    fold.candidate_adverse, fold.comparator_adverse):
                self.assertEqual(metrics.marked_session_count, 40)
                self.assertFalse(metrics.holdout_inspected)
                self.assertFalse(metrics.investment_performance_established)
        self.assertTrue(receipt.metrics_calculated)
        self.assertTrue(receipt.comparator_executed)
        self.assertTrue(receipt.adverse_policy_executed)
        self.assertFalse(receipt.selection_frozen)
        self.assertFalse(receipt.holdout_inspected)

    def test_canonical_receipt_is_hash_bound_and_excludes_ledger_values(self):
        receipt = compose_validation_metric_run(
            self.series, self.config, self.manifest)
        output = receipt.canonical_bytes()
        decoded = output.decode('ascii')
        self.assertEqual(receipt.output_binding(self.manifest).output_sha256,
                         sha256(output).hexdigest())
        self.assertIn('benchmark=buy_and_hold', decoded)
        self.assertIn('metrics=fold-1|candidate_base|', decoded)
        self.assertIn('metrics=fold-2|comparator_adverse|', decoded)
        for prohibited in (
                'open_price', 'close_price', 'execution_price', 'cash_after',
                'shares_after', 'quantity', 'traded_notional'):
            self.assertNotIn(prohibited, decoded)

    def test_manifest_and_configuration_changes_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'unsupported_validation_metric_configuration'):
            compose_validation_metric_run(
                self.series, ExperimentConfig(), self.manifest)
        with self.assertRaisesRegex(
                ValueError, 'validation_metric_manifest_mismatch'):
            compose_validation_metric_run(
                self.series, self.config,
                replace(self.manifest, config_sha256='e' * 64))

    def test_receipt_cannot_promote_selection_holdout_real_data_or_performance(self):
        receipt = compose_validation_metric_run(
            self.series, self.config, self.manifest)
        for change in (
                {'selection_frozen': True}, {'holdout_inspected': True},
                {'real_data_validated': True},
                {'investment_performance_established': True},
                {'comparator_executed': False},
                {'adverse_policy_executed': False},
                {'status': 'validated_performance'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(receipt, **change)

    def test_fold_rejects_misaligned_metric_calendar(self):
        metrics = EvaluationMetrics(
            Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'),
            Decimal('0'), 39)
        with self.assertRaisesRegex(ValueError, 'invalid_validation_metric_fold'):
            ValidationMetricFoldReceipt(
                'fold-1', 80, 120, 35,
                metrics, metrics, metrics, metrics)

    def test_output_binding_rejects_other_manifest(self):
        receipt = compose_validation_metric_run(
            self.series, self.config, self.manifest)
        other = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-metrics-v2',
            code_commit_sha='d' * 40)
        with self.assertRaisesRegex(
                ValueError, 'validation_metric_manifest_mismatch'):
            receipt.output_binding(other)

    def test_checked_in_evidence_matches_feature_commit_and_exact_output(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        checked_manifest = json.loads((
            fixtures / 'm3-validation-metrics-manifest.json').read_text('utf-8'))
        manifest = register_experiment(
            self.series, self.config,
            experiment_id=checked_manifest['experiment_id'],
            code_commit_sha=checked_manifest['code_commit_sha'])
        self.assertEqual(
            checked_manifest,
            {**manifest.__dict__, 'manifest_sha256': manifest.manifest_sha256})

        receipt = compose_validation_metric_run(
            self.series, self.config, manifest)
        binding = receipt.output_binding(manifest)

        def metric(row):
            return {
                name: (format(value, 'f') if isinstance(value, Decimal) else value)
                for name, value in row.__dict__.items()
            }

        expected = {
            'schema_version': receipt.schema_version,
            'experiment_id': receipt.experiment_id,
            'manifest_sha256': receipt.manifest_sha256,
            'status': receipt.status,
            'benchmark': receipt.benchmark,
            'folds': [{
                'fold_id': fold.fold_id,
                'validation_start': fold.validation_start,
                'validation_end': fold.validation_end,
                'eligible_decision_count': fold.eligible_decision_count,
                'candidate_base': metric(fold.candidate_base),
                'comparator_base': metric(fold.comparator_base),
                'candidate_adverse': metric(fold.candidate_adverse),
                'comparator_adverse': metric(fold.comparator_adverse),
            } for fold in receipt.folds],
            'metrics_calculated': receipt.metrics_calculated,
            'comparator_executed': receipt.comparator_executed,
            'adverse_policy_executed': receipt.adverse_policy_executed,
            'selection_frozen': receipt.selection_frozen,
            'holdout_inspected': receipt.holdout_inspected,
            'real_data_validated': receipt.real_data_validated,
            'investment_performance_established':
                receipt.investment_performance_established,
            'output_sha256': binding.output_sha256,
            'output_bytes_count': binding.output_bytes_count,
        }
        checked_receipt = json.loads((
            fixtures / 'm3-validation-metrics-receipt.json').read_text('utf-8'))
        self.assertEqual(checked_receipt, expected)


if __name__ == '__main__':
    unittest.main()
