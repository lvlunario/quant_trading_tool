"""Research work items expose gaps without fabricating progress or evidence."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import unittest

from atlas.research_work_items import compose_research_work_queue
from atlas.rights_evidence import (
    RightsEvidenceItem, RightsEvidenceReport, assess_reviewed_rights,
    load_reviewed_rights_evidence,
)
from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class ResearchWorkItemTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.now = datetime(2026, 10, 5, tzinfo=timezone.utc)
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

    def report(self, rights=None):
        return compose_research_work_queue(
            self.registry, self.catalog, rights or self.rights).public_summary()

    def test_current_queue_distinguishes_each_missing_dependency(self):
        report = self.report()
        self.assertEqual((report['work_item_count'], report['blocked_count']),
                         (9, 9))
        self.assertEqual((report['catalogued_source_count'],
                          report['rights_allowed_count']), (3, 0))
        by_symbol = {item['symbol']: item for item in report['items']}
        self.assertEqual(by_symbol['NVDA']['primary_blocker'],
                         'missing_review_evidence')
        self.assertEqual(by_symbol['QCOM']['primary_blocker'],
                         'source_candidate_missing')
        self.assertEqual(by_symbol['CRBS']['primary_blocker'],
                         'identity_unresolved')

    def test_all_items_withhold_metrics_and_release(self):
        report = self.report()
        self.assertTrue(all(item['status'] == 'blocked' and
                            item['metric_status'] == 'unavailable'
                            for item in report['items']))
        self.assertEqual(report['technical_retrieval_status'],
                         'disabled_separate_gate')
        self.assertFalse(report['release_authorized'])

    def test_rights_permission_still_requires_source_evidence(self):
        permitted = RightsEvidenceReport(
            self.now, tuple(
                RightsEvidenceItem(item.symbol, True, 'explicitly_permitted')
                for item in self.rights.items))
        report = self.report(permitted)
        self.assertEqual(report['rights_allowed_count'], 3)
        catalogued = [item for item in report['items']
                      if item['source_status'] == 'catalogued_public_candidate']
        self.assertTrue(all(item['primary_blocker'] == 'source_evidence_missing'
                            for item in catalogued))
        self.assertTrue(all(item['next_action'] ==
                            'capture_permitted_source_evidence'
                            for item in catalogued))
        self.assertFalse(report['release_authorized'])

    def test_rights_universe_and_assessment_time_must_align(self):
        missing = replace(self.rights, items=self.rights.items[:-1])
        early = replace(self.rights, assessed_at=self.catalog.as_of.replace(day=2))
        for rights in (missing, early):
            with self.subTest(rights=rights), self.assertRaises(ValueError):
                compose_research_work_queue(self.registry, self.catalog, rights)

    def test_public_summary_excludes_evidence_and_financial_fields(self):
        text = str(self.report()).lower()
        for excluded in ('source_uri', 'terms_uri', 'document_id', 'review_id',
                         'reviewer_reference', 'sha256', 'price', 'metric_value',
                         "'recommendation'"):
            self.assertNotIn(excluded, text)

    def test_invalid_operands_are_rejected(self):
        for registry, catalog, rights in (
                (object(), self.catalog, self.rights),
                (self.registry, object(), self.rights),
                (self.registry, self.catalog, object())):
            with self.subTest(), self.assertRaisesRegex(
                    ValueError, 'invalid_research_work_queue_input'):
                compose_research_work_queue(registry, catalog, rights)
