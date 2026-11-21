from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import unittest

from atlas.experiment_registry import (
    ExperimentConfig, ExperimentManifest, ExperimentOutputReceipt,
    bind_synthetic_output, canonical_series_bytes, register_experiment,
)
from atlas.synthetic_execution import SyntheticBar, TargetState
from atlas.synthetic_series import SyntheticSeries, registered_series


class ExperimentRegistryTests(unittest.TestCase):
    def setUp(self):
        self.config = ExperimentConfig()
        self.series = registered_series()
        self.manifest = register_experiment(
            self.series, self.config, experiment_id='m3-synthetic-v1',
            code_commit_sha='a' * 40)

    def test_registered_manifest_is_exact_and_preregistration_only(self):
        self.assertEqual(self.manifest.schema_version, 1)
        self.assertEqual(self.manifest.status, 'preregistered')
        self.assertIsNone(self.manifest.output_sha256)
        self.assertTrue(self.manifest.synthetic_only)
        self.assertFalse(self.manifest.holdout_inspected)
        self.assertFalse(self.manifest.investment_performance_established)
        self.assertEqual(len(self.manifest.config_sha256), 64)
        self.assertEqual(len(self.manifest.input_sha256), 64)
        self.assertEqual(len(self.manifest.manifest_sha256), 64)

    def test_checked_in_manifest_matches_exact_feature_commit(self):
        path = Path(__file__).parents[1] / 'fixtures' / 'm3-experiment-manifest.json'
        checked_in = json.loads(path.read_text(encoding='utf-8'))
        manifest = register_experiment(
            self.series, self.config, experiment_id='m3-synthetic-v1',
            code_commit_sha=checked_in['code_commit_sha'])
        expected = {
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
        self.assertEqual(checked_in, expected)

    def test_series_canonical_bytes_have_independent_small_fixture(self):
        series = SyntheticSeries(
            'atlas.synthetic_series@1.0.0', 7,
            (SyntheticBar(0, Decimal('10.0000'), Decimal('10.5000')),
             SyntheticBar(1, Decimal('10.6000'), Decimal('10.4000'))),
            (TargetState(1, Decimal('0')),), 1)
        expected = (
            b'generator_version=atlas.synthetic_series@1.0.0\n'
            b'seed=7\nlookback_sessions=1\n'
            b'bars=session|open|close\n'
            b'0|10.0000|10.5000\n1|10.6000|10.4000\n'
            b'targets=decision_session|target_exposure\n1|0\n')
        self.assertEqual(canonical_series_bytes(series), expected)
        self.assertEqual(sha256(expected).hexdigest(),
                         sha256(canonical_series_bytes(series)).hexdigest())

    def test_config_hash_changes_for_each_decision_input(self):
        changes = (
            {'holdout_start': 159}, {'lookback_sessions': 19},
            {'initial_cash': Decimal('99999')}, {'base_cost_bps_per_side': 11},
            {'base_delay_sessions': 2}, {'adverse_cost_bps_per_side': 26},
            {'adverse_delay_sessions': 3}, {'label_horizon_sessions': 6},
            {'training_gap_sessions': 2}, {'adverse_overlap_policy': 'fifo'},
        )
        for change in changes:
            with self.subTest(change=change):
                self.assertNotEqual(
                    self.config.config_sha256,
                    replace(self.config, **change).config_sha256)
        self.assertEqual(
            self.config.config_sha256,
            replace(self.config, initial_cash=Decimal('100000.00')).config_sha256)

    def test_adverse_overlap_amendment_is_explicit_and_hash_bound(self):
        amended = replace(self.config, adverse_overlap_policy='fifo')
        self.assertEqual(self.config.config_sha256,
                         '91135464680c078552719e6934f7788899600b9760999ebabebc3f56d761ceea')
        self.assertIn(b'adverse_overlap_policy=fifo\n', amended.canonical_bytes())
        self.assertNotEqual(self.config.config_sha256, amended.config_sha256)
        with self.assertRaisesRegex(
                ValueError, 'unsupported_adverse_overlap_policy'):
            replace(self.config, adverse_overlap_policy='latest')

    def test_series_or_config_change_breaks_manifest_identity(self):
        changed_config = register_experiment(
            self.series, replace(self.config, initial_cash=Decimal('90000')),
            experiment_id='m3-synthetic-v1', code_commit_sha='a' * 40)
        changed_input_hash = sha256(canonical_series_bytes(
            replace(self.series, seed=self.series.seed + 1))).hexdigest()
        self.assertNotEqual(self.manifest.input_sha256, changed_input_hash)
        self.assertNotEqual(self.manifest.manifest_sha256,
                            changed_config.manifest_sha256)

    def test_registration_reproduces_seeded_bars_and_targets(self):
        for altered in (
                replace(self.series, seed=self.series.seed + 1),
                replace(self.series, bars=(replace(
                    self.series.bars[0], close_price=Decimal('1')),) +
                    self.series.bars[1:]),
                replace(self.series, targets=self.series.targets[:-1])):
            with self.subTest(altered=altered), self.assertRaisesRegex(
                    ValueError, 'experiment_series_reproduction_mismatch'):
                register_experiment(
                    altered, self.config, experiment_id='m3-synthetic-v1',
                    code_commit_sha='a' * 40)

    def test_registration_rejects_holdout_or_performance_promotion(self):
        for unsafe in (
                replace(self.series, holdout_inspected=True),
                replace(self.series, investment_performance_established=True),
                replace(self.series, targets=self.series.targets +
                        (TargetState(160, Decimal('1')),))):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                register_experiment(
                    unsafe, self.config, experiment_id='m3-synthetic-v1',
                    code_commit_sha='a' * 40)

    def test_invalid_identifiers_and_manifest_states_fail_closed(self):
        for kwargs in (
                {'experiment_id': 'bad'}, {'code_commit_sha': 'short'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                register_experiment(self.series, self.config,
                                    experiment_id=kwargs.get(
                                        'experiment_id', 'm3-synthetic-v1'),
                                    code_commit_sha=kwargs.get(
                                        'code_commit_sha', 'a' * 40))
        for change in (
                {'status': 'complete'}, {'output_sha256': 'b' * 64},
                {'holdout_inspected': True},
                {'investment_performance_established': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.manifest, **change)

    def test_output_receipt_binds_exact_opaque_bytes(self):
        output = b'{"status":"synthetic_plumbing_only"}\n'
        receipt = bind_synthetic_output(self.manifest, output)
        self.assertEqual(receipt.manifest_sha256,
                         self.manifest.manifest_sha256)
        self.assertEqual(receipt.output_sha256, sha256(output).hexdigest())
        self.assertEqual(receipt.output_bytes_count, len(output))
        self.assertFalse(receipt.holdout_inspected)
        self.assertFalse(receipt.investment_performance_established)
        self.assertNotEqual(
            receipt.output_sha256,
            bind_synthetic_output(self.manifest, output + b' ').output_sha256)

    def test_output_binding_rejects_empty_or_promoted_states(self):
        for value in (b'', 'not-bytes', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bind_synthetic_output(self.manifest, value)
        for change in (
                {'holdout_inspected': True},
                {'investment_performance_established': True},
                {'status': 'performance_validated'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                ExperimentOutputReceipt(
                    self.manifest.manifest_sha256, 'b' * 64, 1, **change)


if __name__ == '__main__':
    unittest.main()
