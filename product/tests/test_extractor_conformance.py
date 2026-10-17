from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.extractor_conformance import evaluate_synthetic_extractor


class ExtractorConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = (Path(__file__).parents[1] / 'fixtures' /
                   'synthetic-extractor-conformance.json')
        cls.manifest = json.loads(fixture.read_bytes())
        cls.now = datetime(2026, 9, 30, tzinfo=timezone.utc)

    def evaluate(self, manifest=None):
        payload = self.manifest if manifest is None else manifest
        return evaluate_synthetic_extractor(
            json.dumps(payload).encode(), now=self.now)

    def test_fixed_suite_passes_zero_tolerance_policy(self):
        report = self.evaluate()
        self.assertEqual(report['status'], 'conformant_synthetic')
        self.assertEqual(report['case_count'], 6)
        self.assertEqual(report['matched_case_count'], 6)
        self.assertEqual((report['false_accept_count'], report['false_reject_count'],
                          report['contract_mismatch_count']), (0, 0, 0))
        self.assertEqual(report['missing_categories'], [])

    def test_false_accept_is_explicit_and_blocks(self):
        manifest = deepcopy(self.manifest)
        case = next(case for case in manifest['cases'] if case['category'] == 'nominal')
        case['expected'] = {'status': 'blocked', 'code': 'metric_unavailable',
                            'value': None}
        report = self.evaluate(manifest)
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['false_accept_count'], 1)
        self.assertIn('false_accept_limit_exceeded', report['codes'])

    def test_false_reject_is_explicit_and_blocks(self):
        manifest = deepcopy(self.manifest)
        case = next(case for case in manifest['cases'] if case['category'] == 'missing')
        case['expected'] = {'status': 'accepted', 'code': 'ready', 'value': '123.40'}
        report = self.evaluate(manifest)
        self.assertEqual(report['false_reject_count'], 1)
        self.assertIn('false_reject_limit_exceeded', report['codes'])

    def test_wrong_expected_value_is_contract_mismatch(self):
        manifest = deepcopy(self.manifest)
        manifest['cases'][0]['expected']['value'] = '999'
        report = self.evaluate(manifest)
        self.assertEqual(report['contract_mismatch_count'], 1)
        self.assertIn('contract_mismatch_limit_exceeded', report['codes'])

    def test_case_count_and_category_coverage_are_enforced(self):
        manifest = deepcopy(self.manifest)
        manifest['cases'] = manifest['cases'][:-1]
        report = self.evaluate(manifest)
        self.assertIn('insufficient_case_count', report['codes'])
        self.assertIn('missing_required_categories', report['codes'])
        self.assertEqual(report['missing_categories'], ['period'])

    def test_manifest_contract_rejects_ambiguity(self):
        for mutate, code in (
            (lambda value: value.update(extra=True), 'invalid_conformance_manifest_schema'),
            (lambda value: value.__setitem__('provider_id', 'PRV_OTHER1234'),
             'unsupported_synthetic_extractor_profile'),
            (lambda value: value['expected_metric'].update(
                unit='ratio', currency='USD'), 'invalid_extractor_metric_semantics'),
            (lambda value: value['cases'][1].__setitem__(
                'case_id', value['cases'][0]['case_id']), 'duplicate_conformance_case_id'),
        ):
            manifest = deepcopy(self.manifest)
            mutate(manifest)
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, code):
                self.evaluate(manifest)

    def test_report_contains_no_source_documents(self):
        report = self.evaluate()
        encoded = json.dumps(report)
        for private_field in ('"source"', '"formula"', '"period_start"',
                              'Reported revenue', 'Wrong metric'):
            self.assertNotIn(private_field, encoded)


if __name__ == '__main__':
    unittest.main()
