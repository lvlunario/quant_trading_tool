from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import unittest

from atlas.source_workflow import synthetic_source_report


class SyntheticSourceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.fixture = (Path(__file__).parents[1] / 'fixtures' /
                        'synthetic-research-source.json')
        self.source_bytes = self.fixture.read_bytes()
        self.now = datetime(2026, 9, 29, tzinfo=timezone.utc)

    def report(self, source_bytes=None, rights=None):
        return synthetic_source_report(
            self.source_bytes if source_bytes is None else source_bytes,
            now=self.now, rights=rights)

    def test_fixture_runs_exact_source_to_ready_metric(self):
        report = self.report()
        self.assertEqual((report['mode'], report['status']), ('synthetic', 'ready'))
        self.assertEqual(report['source_sha256'], sha256(self.source_bytes).hexdigest())
        self.assertEqual(report['metric']['value'], '123.40')
        self.assertEqual(report['metric']['period_end'], '2026-06-30')
        self.assertEqual(report['extraction']['status'], 'ready')
        self.assertEqual(report['extraction']['method'], 'deterministic_parser')
        self.assertEqual(report['extraction']['review_status'], 'not_required')
        self.assertIn('all synthetic source gates passed', report['readiness'])

    def test_missing_rights_block_before_metric_release(self):
        report = self.report(b'{not-json', rights=[])
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['codes'], ['rights_missing_evidence'])
        self.assertIsNone(report['source_sha256'])
        self.assertIsNone(report['metric'])

    def test_missing_metric_is_not_converted_to_zero(self):
        raw = json.loads(self.source_bytes)
        raw['metric']['value'] = None
        raw['metric']['missing_reason'] = 'missing_source'
        report = self.report(json.dumps(raw).encode())
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['codes'], ['metric_unavailable'])
        self.assertIsNone(report['metric'])

    def test_changed_source_bytes_change_exact_digest(self):
        raw = json.loads(self.source_bytes)
        raw['metric']['value'] = '124.00'
        changed = json.dumps(raw, separators=(',', ':')).encode()
        report = self.report(changed)
        self.assertEqual(report['status'], 'ready')
        self.assertEqual(report['metric']['value'], '124.00')
        self.assertEqual(report['source_sha256'], sha256(changed).hexdigest())
        self.assertNotEqual(report['source_sha256'], sha256(self.source_bytes).hexdigest())

    def test_malformed_and_extended_contracts_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'invalid_synthetic_source_json'):
            self.report(b'{')
        raw = json.loads(self.source_bytes)
        raw['unexpected'] = 'PRIVATE-MARKER'
        with self.assertRaisesRegex(ValueError, 'invalid_synthetic_source_schema'):
            self.report(json.dumps(raw).encode())


if __name__ == '__main__':
    unittest.main()
