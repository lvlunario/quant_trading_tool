"""Blank rights-review worksheets enumerate work without fabricating evidence."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import unittest

from atlas.rights_evidence import REVIEW_CHECKLIST
from atlas.rights_review_worksheet import (
    ALLOWED_ACTIONS, ALLOWED_CONCLUSIONS, EVIDENCE_SLOTS,
    build_rights_review_worksheet,
)
from atlas.source_catalog import load_public_source_catalog
from atlas.source_rights import load_source_rights_manifest
from atlas.watchlist_registry import load_public_watchlist_registry


class RightsReviewWorksheetTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(), now=now)
        self.catalog = load_public_source_catalog(
            (fixtures / 'public-research-sources.json').read_bytes(),
            registry, now=now)
        self.manifest = load_source_rights_manifest(
            (fixtures / 'public-source-rights-review.json').read_bytes(),
            self.catalog, now=now)

    def test_template_covers_exact_catalog_with_blank_review_state(self):
        report = build_rights_review_worksheet(
            self.catalog, self.manifest).template_summary()
        self.assertEqual((report['status'], report['candidate_count']),
                         ('blocked', 8))
        self.assertEqual([item['symbol'] for item in report['items']],
                         ['NVDA', 'MU', 'AVGO', 'QCOM', 'PLTR', 'SPCX',
                          'QBTS', 'RGTI'])
        self.assertTrue(all(item['review_state'] == 'not_started'
                            for item in report['items']))
        self.assertTrue(all(item['source_uri'].startswith('https://')
                            for item in report['items']))

    def test_template_declares_exact_evidence_contract_without_values(self):
        report = build_rights_review_worksheet(
            self.catalog, self.manifest).template_summary()
        self.assertEqual(report['evidence_slots'], list(EVIDENCE_SLOTS))
        self.assertEqual(report['allowed_conclusions'], list(ALLOWED_CONCLUSIONS))
        self.assertEqual(report['allowed_actions'], list(ALLOWED_ACTIONS))
        self.assertEqual(report['checklist'], [
            {'item': item, 'status': 'pending'} for item in REVIEW_CHECKLIST])
        self.assertEqual(report['evidence_storage'], 'private_outside_repository')
        self.assertFalse(report['release_authorized'])

    def test_public_readiness_is_count_only_and_blocked(self):
        report = build_rights_review_worksheet(
            self.catalog, self.manifest).public_readiness_summary()
        self.assertEqual(report, {
            'schema_version': 1,
            'status': 'blocked',
            'review_task_count': 8,
            'pending_review_count': 8,
            'required_check_count': 64,
            'completed_check_count': 0,
            'pending_check_count': 64,
            'evidence_storage': 'private_outside_repository',
            'technical_retrieval_status': 'disabled_separate_gate',
            'release_authorized': False,
            'next_action': 'complete_manual_terms_review_privately',
        })
        serialized = str(report).lower()
        for private_field in ('source_uri', 'document_id', 'terms_uri',
                              'evidence_sha256', 'reviewer_reference',
                              'review_id'):
            self.assertNotIn(private_field, serialized)

    def test_misaligned_or_promoted_manifest_fails_closed(self):
        missing = replace(self.manifest, reviews=self.manifest.reviews[:-1])
        promoted_review = replace(self.manifest.reviews[0], review_state='complete')
        promoted = replace(
            self.manifest,
            reviews=(promoted_review,) + self.manifest.reviews[1:])
        for manifest in (missing, promoted):
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                build_rights_review_worksheet(self.catalog, manifest)

    def test_invalid_operands_are_rejected(self):
        for catalog, manifest in (
                (object(), self.manifest), (self.catalog, object())):
            with self.subTest(), self.assertRaisesRegex(
                    ValueError, 'invalid_rights_review_worksheet_input'):
                build_rights_review_worksheet(catalog, manifest)
