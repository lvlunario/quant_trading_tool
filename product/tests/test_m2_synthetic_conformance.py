"""Synthetic M2 conformance stays separate from public-source readiness."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.m2_acceptance_trace import build_m2_acceptance_trace
from atlas.m2_synthetic_conformance import assess_m2_synthetic_conformance
from atlas.rights_evidence import (
    assess_reviewed_rights, load_reviewed_rights_evidence,
)
from atlas.source_capture_authorization import assess_source_capture_authorization
from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class M2SyntheticConformanceTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).parents[1] / 'fixtures'
        self.now = datetime(2026, 10, 8, tzinfo=timezone.utc)
        registry = load_public_watchlist_registry(
            (self.fixtures / 'public-watchlist-identities.json').read_bytes(),
            now=self.now)
        catalog = load_public_source_catalog(
            (self.fixtures / 'public-research-sources.json').read_bytes(),
            registry, now=self.now)
        evidence = load_reviewed_rights_evidence(
            (self.fixtures / 'public-source-rights-evidence.json').read_bytes(),
            catalog, now=self.now)
        rights = assess_reviewed_rights(catalog, evidence, at=self.now)
        capture = assess_source_capture_authorization(catalog, rights, at=self.now)
        self.public_trace = build_m2_acceptance_trace(
            registry, catalog, rights, capture)
        self.synthetic_bytes = (
            self.fixtures / 'synthetic-research-source.json').read_bytes()

    def report(self, source_bytes=None):
        return assess_m2_synthetic_conformance(
            self.synthetic_bytes if source_bytes is None else source_bytes,
            self.public_trace, now=self.now)

    def test_invented_scenario_passes_all_six_technical_gates(self):
        report = self.report()
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(
            [stage['gate'] for stage in report['synthetic_scenario']['stages']],
            ['identity', 'source_discovery', 'rights_review',
             'capture_authorization', 'extraction', 'metric_release'])
        self.assertTrue(all(
            stage['status'] == 'passed'
            for stage in report['synthetic_scenario']['stages']))

    def test_public_source_release_state_remains_blocked(self):
        report = self.report()
        self.assertEqual(report['public_source_state']['status'], 'blocked')
        self.assertEqual(report['public_source_state']['passed_counts'],
                         [8, 8, 0, 0, 0, 0])
        self.assertEqual(report['public_source_state']['extraction_passed_count'], 0)
        self.assertEqual(report['public_source_state']['metric_release_passed_count'], 0)
        self.assertFalse(report['release_authorized'])
        self.assertFalse(report['milestone_acceptance_recorded'])

    def test_blocked_synthetic_workflow_fails_conformance(self):
        raw = json.loads(self.synthetic_bytes)
        raw['metric']['value'] = None
        raw['metric']['missing_reason'] = 'missing_source'
        report = self.report(json.dumps(raw).encode())
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['failed_checks'], ['synthetic_workflow_blocked'])
        self.assertTrue(all(
            stage['status'] == 'not_demonstrated'
            for stage in report['synthetic_scenario']['stages']))

    def test_summary_excludes_source_and_financial_evidence(self):
        serialized = str(self.report()).lower()
        for excluded in ('document_id', 'observation_id', 'source_sha256',
                         'source_uri', 'terms_uri', 'metric_id', 'metric_value',
                         '123.40', 'symbol', 'price', 'quantity', 'account'):
            self.assertNotIn(excluded, serialized)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'invalid_m2_synthetic_conformance_input'):
            assess_m2_synthetic_conformance(
                'not-bytes', self.public_trace, now=self.now)


if __name__ == '__main__':
    unittest.main()
