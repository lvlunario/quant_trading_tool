"""M2 trace composes gates without promoting unavailable evidence."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import unittest

from atlas.m2_acceptance_trace import build_m2_acceptance_trace
from atlas.rights_evidence import (
    RightsEvidenceItem, RightsEvidenceReport, assess_reviewed_rights,
    load_reviewed_rights_evidence,
)
from atlas.source_capture_authorization import (
    SourceCaptureAuthorizationItem, assess_source_capture_authorization,
)
from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class M2AcceptanceTraceTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.now = datetime(2026, 10, 7, tzinfo=timezone.utc)
        self.registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(),
            now=self.now)
        self.catalog = load_public_source_catalog(
            (fixtures / 'public-research-sources.json').read_bytes(),
            self.registry, now=self.now)
        evidence = load_reviewed_rights_evidence(
            (fixtures / 'public-source-rights-evidence.json').read_bytes(),
            self.catalog, now=self.now)
        self.rights = assess_reviewed_rights(
            self.catalog, evidence, at=self.now)
        self.capture = assess_source_capture_authorization(
            self.catalog, self.rights, at=self.now)

    def report(self, rights=None, capture=None):
        return build_m2_acceptance_trace(
            self.registry, self.catalog, rights or self.rights,
            capture or self.capture).public_summary()

    def test_current_trace_reports_every_gate_in_order(self):
        report = self.report()
        self.assertEqual([item['gate'] for item in report['stages']], [
            'identity', 'source_discovery', 'rights_review',
            'capture_authorization', 'extraction', 'metric_release'])
        self.assertEqual([item['passed_count'] for item in report['stages']],
                         [8, 8, 0, 0, 0, 0])
        self.assertTrue(all(item['passed_count'] + item['blocked_count'] == 9
                            for item in report['stages']))

    def test_trace_never_records_acceptance_or_release(self):
        report = self.report()
        self.assertEqual(report['status'], 'blocked')
        self.assertFalse(report['milestone_acceptance_recorded'])
        self.assertFalse(report['release_authorized'])
        self.assertEqual(report['stages'][-1]['blocker'],
                         'no_verified_metric_evidence')

    def test_rights_progress_cannot_promote_later_gates(self):
        rights = RightsEvidenceReport(
            self.now, tuple(RightsEvidenceItem(
                item.symbol, True, 'explicitly_permitted')
                for item in self.catalog.candidates))
        capture = assess_source_capture_authorization(
            self.catalog, rights, at=self.now)
        report = self.report(rights, capture)
        self.assertEqual([item['passed_count'] for item in report['stages']],
                         [8, 8, 8, 0, 0, 0])

    def test_misaligned_receipt_fails_closed(self):
        altered = replace(
            self.capture,
            items=(SourceCaptureAuthorizationItem(
                self.capture.items[0].symbol, True, True,
                'source_capture_authorized'),) + self.capture.items[1:])
        with self.assertRaisesRegex(ValueError,
                                    'inconsistent_m2_acceptance_trace_input'):
            build_m2_acceptance_trace(
                self.registry, self.catalog, self.rights, altered)

    def test_public_trace_excludes_evidence_and_financial_fields(self):
        serialized = str(self.report()).lower()
        for excluded in ('symbol', 'source_uri', 'terms_uri', 'document_id',
                         'authorization_id', 'review_id', 'sha256', 'metric_value',
                         'price', 'quantity', 'account', 'recommendation'):
            self.assertNotIn(excluded, serialized)


if __name__ == '__main__':
    unittest.main()
