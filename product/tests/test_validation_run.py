from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import unittest

from atlas.experiment_registry import ExperimentConfig, register_experiment
from atlas.validation_run import (
    AdverseValidationRunReceipt, ComparatorFoldReceipt,
    ComparatorValidationRunReceipt, ValidationFoldReceipt, ValidationRunReceipt,
    compose_adverse_validation_run, compose_comparator_validation_run,
    compose_validation_run,
)
from atlas.synthetic_series import registered_series


class ValidationRunTests(unittest.TestCase):
    def setUp(self):
        self.series = registered_series()
        self.config = ExperimentConfig()
        self.manifest = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-validation-v1',
            code_commit_sha='a' * 40)

    def test_registered_validation_composes_exact_structural_counts(self):
        receipt = compose_validation_run(
            self.series, self.config, self.manifest)
        self.assertEqual(receipt.folds, (
            ValidationFoldReceipt('fold-1', 80, 120, 74, 35, 11, 80, 5, 5),
            ValidationFoldReceipt('fold-2', 120, 160, 114, 35, 11, 40, 2, 2),
        ))
        self.assertEqual(receipt.base_cost_bps_per_side, 10)
        self.assertEqual(receipt.base_delay_sessions, 1)

    def test_canonical_receipt_is_independently_specified_and_hash_bound(self):
        receipt = compose_validation_run(
            self.series, self.config, self.manifest)
        expected = (
            b'schema_version=1\n'
            b'experiment_id=m3-synthetic-validation-v1\n'
            b'manifest_sha256=' + self.manifest.manifest_sha256.encode('ascii') +
            b'\nstatus=synthetic_plumbing_only\nbase_policy=10|1\n'
            b'fold=fold-1|80|120|74|35|11|80|5|5\n'
            b'fold=fold-2|120|160|114|35|11|40|2|2\n'
            b'comparator_executed=false\nadverse_policy_executed=false\n'
            b'adverse_blocker=overlapping_execution_policy_undefined\n'
            b'metrics_calculated=false\nholdout_inspected=false\n'
            b'investment_performance_established=false\n')
        self.assertEqual(receipt.canonical_bytes(), expected)
        binding = receipt.output_binding(self.manifest)
        self.assertEqual(binding.output_sha256, sha256(expected).hexdigest())
        self.assertEqual(binding.output_bytes_count, len(expected))

    def test_checked_in_manifest_and_receipt_match_feature_commit(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        checked_manifest = json.loads(
            (fixtures / 'm3-validation-manifest.json').read_text('utf-8'))
        manifest = register_experiment(
            self.series, self.config,
            experiment_id=checked_manifest['experiment_id'],
            code_commit_sha=checked_manifest['code_commit_sha'])
        expected_manifest = {
            'schema_version': manifest.schema_version,
            'experiment_id': manifest.experiment_id,
            'protocol_version': manifest.protocol_version,
            'code_commit_sha': manifest.code_commit_sha,
            'generator_version': manifest.generator_version,
            'config_sha256': manifest.config_sha256,
            'input_sha256': manifest.input_sha256,
            'status': manifest.status,
            'output_sha256': manifest.output_sha256,
            'synthetic_only': manifest.synthetic_only,
            'holdout_inspected': manifest.holdout_inspected,
            'investment_performance_established':
                manifest.investment_performance_established,
            'manifest_sha256': manifest.manifest_sha256,
        }
        self.assertEqual(checked_manifest, expected_manifest)

        receipt = compose_validation_run(self.series, self.config, manifest)
        binding = receipt.output_binding(manifest)
        checked_receipt = json.loads(
            (fixtures / 'm3-validation-receipt.json').read_text('utf-8'))
        expected_receipt = {
            'schema_version': receipt.schema_version,
            'experiment_id': receipt.experiment_id,
            'manifest_sha256': receipt.manifest_sha256,
            'status': receipt.status,
            'base_cost_bps_per_side': receipt.base_cost_bps_per_side,
            'base_delay_sessions': receipt.base_delay_sessions,
            'folds': [row.__dict__ for row in receipt.folds],
            'comparator_executed': receipt.comparator_executed,
            'adverse_policy_executed': receipt.adverse_policy_executed,
            'adverse_blocker': receipt.adverse_blocker,
            'metrics_calculated': receipt.metrics_calculated,
            'holdout_inspected': receipt.holdout_inspected,
            'investment_performance_established':
                receipt.investment_performance_established,
            'output_sha256': binding.output_sha256,
            'output_bytes_count': binding.output_bytes_count,
        }
        self.assertEqual(checked_receipt, expected_receipt)

    def test_comparator_uses_same_calendar_under_both_policies(self):
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-comparator-v1',
            code_commit_sha='c' * 40)
        receipt = compose_comparator_validation_run(
            self.series, config, manifest)
        self.assertEqual(receipt.folds, (
            ComparatorFoldReceipt('fold-1', 80, 120, 35, 119, 1, 1, 1, 1),
            ComparatorFoldReceipt('fold-2', 120, 160, 35, 159, 1, 1, 1, 1),
        ))
        self.assertTrue(receipt.comparator_executed)
        self.assertTrue(receipt.base_comparator_executed)
        self.assertTrue(receipt.adverse_comparator_executed)
        self.assertFalse(receipt.metrics_calculated)
        self.assertFalse(receipt.holdout_inspected)

    def test_comparator_receipt_is_structural_and_hash_bound(self):
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-comparator-v1',
            code_commit_sha='c' * 40)
        receipt = compose_comparator_validation_run(
            self.series, config, manifest)
        output = receipt.canonical_bytes().decode('ascii')
        self.assertIn('comparator=buy_and_hold', output)
        self.assertIn('base_policy=10|1', output)
        self.assertIn('adverse_policy=25|2|fifo', output)
        for prohibited in ('ending_cash', 'ending_shares', 'marked_value',
                           'return=', 'drawdown=', 'turnover=', 'exposure='):
            self.assertNotIn(prohibited, output)
        binding = receipt.output_binding(manifest)
        self.assertEqual(
            binding.output_sha256,
            sha256(receipt.canonical_bytes()).hexdigest())

    def test_comparator_rejects_unamended_or_mismatched_registration(self):
        with self.assertRaisesRegex(
                ValueError, 'unsupported_comparator_validation_configuration'):
            compose_comparator_validation_run(
                self.series, self.config, self.manifest)
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-comparator-v1',
            code_commit_sha='c' * 40)
        with self.assertRaisesRegex(
                ValueError, 'comparator_validation_manifest_mismatch'):
            compose_comparator_validation_run(
                self.series, config,
                replace(manifest, input_sha256='d' * 64))

    def test_comparator_receipt_cannot_promote_performance_or_holdout(self):
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-comparator-v1',
            code_commit_sha='c' * 40)
        receipt = compose_comparator_validation_run(
            self.series, config, manifest)
        for change in (
                {'metrics_calculated': True}, {'holdout_inspected': True},
                {'investment_performance_established': True},
                {'base_comparator_executed': False},
                {'adverse_comparator_executed': False},
                {'status': 'validated_performance'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(receipt, **change)
        with self.assertRaises(ValueError):
            ComparatorValidationRunReceipt(
                receipt.experiment_id, receipt.manifest_sha256, receipt.folds,
                'cash', 10, 1, 25, 2, 'fifo')

    def test_receipt_discloses_unrun_work_without_financial_values(self):
        receipt = compose_validation_run(
            self.series, self.config, self.manifest)
        self.assertFalse(receipt.comparator_executed)
        self.assertFalse(receipt.adverse_policy_executed)
        self.assertFalse(receipt.metrics_calculated)
        self.assertFalse(receipt.holdout_inspected)
        self.assertFalse(receipt.investment_performance_established)
        output = receipt.canonical_bytes().decode('ascii')
        for prohibited in ('ending_cash', 'ending_shares', 'marked_value',
                           'return=', 'drawdown=', 'turnover=', 'exposure='):
            self.assertNotIn(prohibited, output)

    def test_manifest_or_protocol_changes_fail_before_composition(self):
        for config in (
                replace(self.config, initial_cash=Decimal('90000')),
                replace(self.config, base_cost_bps_per_side=11)):
            with self.subTest(config=config), self.assertRaises(ValueError):
                compose_validation_run(self.series, config, self.manifest)
        with self.assertRaisesRegex(ValueError, 'validation_manifest_mismatch'):
            compose_validation_run(
                self.series, self.config,
                replace(self.manifest, config_sha256='b' * 64))

    def test_output_binding_rejects_a_different_manifest(self):
        receipt = compose_validation_run(
            self.series, self.config, self.manifest)
        other = register_experiment(
            self.series, self.config,
            experiment_id='m3-synthetic-validation-v2',
            code_commit_sha='a' * 40)
        with self.assertRaisesRegex(ValueError, 'validation_manifest_mismatch'):
            receipt.output_binding(other)

    def test_promoted_or_malformed_receipts_fail_closed(self):
        receipt = compose_validation_run(
            self.series, self.config, self.manifest)
        for change in (
                {'comparator_executed': True}, {'adverse_policy_executed': True},
                {'metrics_calculated': True}, {'holdout_inspected': True},
                {'investment_performance_established': True},
                {'status': 'validated_performance'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(receipt, **change)
        with self.assertRaises(ValueError):
            ValidationFoldReceipt('fold-1', 80, 120, 1, 1, 0, 0, 1, 2)

    def test_registered_adverse_run_uses_hash_bound_fifo_without_metrics(self):
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-adverse-v1',
            code_commit_sha='b' * 40)
        receipt = compose_adverse_validation_run(self.series, config, manifest)
        self.assertEqual(receipt.folds, (
            ValidationFoldReceipt('fold-1', 80, 120, 74, 35, 11, 80, 5, 5),
            ValidationFoldReceipt('fold-2', 120, 160, 114, 35, 11, 40, 2, 2),
        ))
        self.assertEqual(receipt.adverse_cost_bps_per_side, 25)
        self.assertEqual(receipt.adverse_delay_sessions, 2)
        self.assertEqual(receipt.adverse_overlap_policy, 'fifo')
        self.assertTrue(receipt.adverse_policy_executed)
        self.assertFalse(receipt.comparator_executed)
        self.assertFalse(receipt.metrics_calculated)
        self.assertFalse(receipt.holdout_inspected)
        output = receipt.canonical_bytes().decode('ascii')
        self.assertIn('adverse_policy=25|2|fifo', output)
        for prohibited in ('ending_cash', 'ending_shares', 'marked_value',
                           'return=', 'drawdown=', 'turnover=', 'exposure='):
            self.assertNotIn(prohibited, output)

    def test_adverse_run_rejects_unamended_or_mismatched_registration(self):
        with self.assertRaisesRegex(
                ValueError, 'unsupported_adverse_validation_configuration'):
            compose_adverse_validation_run(
                self.series, self.config, self.manifest)
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-adverse-v1',
            code_commit_sha='b' * 40)
        with self.assertRaisesRegex(
                ValueError, 'adverse_validation_manifest_mismatch'):
            compose_adverse_validation_run(
                self.series, config,
                replace(manifest, config_sha256='c' * 64))

    def test_adverse_receipt_cannot_promote_unrun_work(self):
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id='m3-synthetic-adverse-v1',
            code_commit_sha='b' * 40)
        receipt = compose_adverse_validation_run(self.series, config, manifest)
        for change in (
                {'comparator_executed': True}, {'adverse_policy_executed': False},
                {'adverse_cost_bps_per_side': 24},
                {'adverse_delay_sessions': 1},
                {'metrics_calculated': True}, {'holdout_inspected': True},
                {'investment_performance_established': True},
                {'status': 'validated_performance'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(receipt, **change)
        with self.assertRaises(ValueError):
            AdverseValidationRunReceipt(
                receipt.experiment_id, receipt.manifest_sha256, receipt.folds,
                25, 2, 'latest')

    def test_checked_in_adverse_amendment_matches_feature_commit(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        checked_manifest = json.loads((
            fixtures / 'm3-adverse-validation-manifest.json').read_text('utf-8'))
        config = replace(self.config, adverse_overlap_policy='fifo')
        manifest = register_experiment(
            self.series, config,
            experiment_id=checked_manifest['experiment_id'],
            code_commit_sha=checked_manifest['code_commit_sha'])
        expected_manifest = {
            **manifest.__dict__, 'manifest_sha256': manifest.manifest_sha256}
        self.assertEqual(checked_manifest, expected_manifest)

        receipt = compose_adverse_validation_run(self.series, config, manifest)
        binding = receipt.output_binding(manifest)
        checked_receipt = json.loads((
            fixtures / 'm3-adverse-validation-receipt.json').read_text('utf-8'))
        expected_receipt = {
            **receipt.__dict__,
            'folds': [row.__dict__ for row in receipt.folds],
            'output_sha256': binding.output_sha256,
            'output_bytes_count': binding.output_bytes_count,
        }
        self.assertEqual(checked_receipt, expected_receipt)


if __name__ == '__main__':
    unittest.main()
