"""Source capture requires independent rights and technical authorization."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from atlas.rights_evidence import RightsEvidenceItem, RightsEvidenceReport
from atlas.source_capture_authorization import (
    TechnicalCaptureApproval, assess_source_capture_authorization,
)
from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class SourceCaptureAuthorizationTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.now = datetime(2026, 10, 6, 11, tzinfo=timezone.utc)
        registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(),
            now=self.now)
        self.catalog = load_public_source_catalog(
            (fixtures / 'public-research-sources.json').read_bytes(), registry,
            now=self.now)
        self.blocked_rights = RightsEvidenceReport(
            self.now, tuple(RightsEvidenceItem(
                item.symbol, False, 'missing_review_evidence')
                for item in self.catalog.candidates))
        candidate = self.catalog.candidates[0]
        self.approval = TechnicalCaptureApproval(
            'AUTH_SYNTH2026100601', candidate.document_id, candidate.symbol,
            'internal_research', 'retrieve_once',
            self.now - timedelta(hours=1), self.now + timedelta(days=1),
            5 * 1024 * 1024,
            ('text/html', 'application/pdf', 'application/json'), False, False)

    def test_empty_public_evidence_blocks_every_capture(self):
        report = assess_source_capture_authorization(
            self.catalog, self.blocked_rights, at=self.now).public_summary()
        self.assertEqual((report['status'], report['candidate_count']),
                         ('blocked', 8))
        self.assertEqual((report['rights_ready_count'],
                          report['capture_authorized_count']), (0, 0))
        self.assertTrue(all(item['decision'] == 'missing_review_evidence'
                            for item in report['items']))
        self.assertFalse(report['release_authorized'])

    def test_rights_without_technical_approval_remain_blocked(self):
        rights = RightsEvidenceReport(
            self.now, tuple(RightsEvidenceItem(
                item.symbol, True, 'explicitly_permitted')
                for item in self.catalog.candidates))
        report = assess_source_capture_authorization(
            self.catalog, rights, at=self.now).public_summary()
        self.assertEqual((report['rights_ready_count'],
                          report['capture_authorized_count']), (8, 0))
        self.assertTrue(all(item['decision'] == 'technical_approval_missing'
                            for item in report['items']))

    def test_exact_current_approval_authorizes_capture_not_release(self):
        rights = replace(
            self.blocked_rights,
            items=(RightsEvidenceItem(
                self.catalog.candidates[0].symbol, True, 'explicitly_permitted'),) +
            self.blocked_rights.items[1:])
        report = assess_source_capture_authorization(
            self.catalog, rights, [self.approval], at=self.now).public_summary()
        self.assertEqual(report['capture_authorized_count'], 1)
        self.assertEqual(report['items'][0]['decision'],
                         'source_capture_authorized')
        self.assertEqual(report['source_bytes_status'], 'not_provided')
        self.assertFalse(report['release_authorized'])

    def test_expired_or_future_approval_is_not_authorized(self):
        rights = replace(
            self.blocked_rights,
            items=(RightsEvidenceItem(
                self.catalog.candidates[0].symbol, True, 'explicitly_permitted'),) +
            self.blocked_rights.items[1:])
        cases = (
            (replace(self.approval, valid_until=self.now),
             'technical_approval_expired'),
            (replace(self.approval,
                     approved_at=self.now + timedelta(hours=1),
                     valid_until=self.now + timedelta(hours=2)),
             'technical_approval_not_yet_effective'),
        )
        for approval, decision in cases:
            with self.subTest(decision=decision):
                report = assess_source_capture_authorization(
                    self.catalog, rights, [approval], at=self.now).public_summary()
                self.assertFalse(report['items'][0]['capture_authorized'])
                self.assertEqual(report['items'][0]['decision'], decision)

    def test_unsafe_or_misaligned_approval_fails_closed(self):
        unsafe = (
            dict(follow_redirects=True),
            dict(retain_source_bytes=True),
            dict(max_source_bytes=5 * 1024 * 1024 + 1),
            dict(allowed_content_types=('application/octet-stream',)),
        )
        for changes in unsafe:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.approval, **changes)
        with self.assertRaisesRegex(ValueError,
                                    'technical_capture_catalog_mismatch'):
            assess_source_capture_authorization(
                self.catalog, self.blocked_rights,
                [replace(self.approval, document_id='DOC_UNKNOWN20261006')],
                at=self.now)

    def test_public_receipt_excludes_private_approval_and_source_fields(self):
        report = assess_source_capture_authorization(
            self.catalog, self.blocked_rights, at=self.now).public_summary()
        serialized = str(report).lower()
        for excluded in ('authorization_id', 'document_id', 'source_uri',
                         'terms_uri', 'evidence_sha256', 'reviewer_reference'):
            self.assertNotIn(excluded, serialized)


if __name__ == '__main__':
    unittest.main()
