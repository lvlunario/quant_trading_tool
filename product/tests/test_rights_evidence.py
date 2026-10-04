"""Reviewed terms evidence is explicit, complete and public-safe."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from atlas.rights_evidence import (
    REVIEW_CHECKLIST, ReviewedRightsEvidence, assess_reviewed_rights,
    load_reviewed_rights_evidence,
)
from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class ReviewedRightsEvidenceTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.now = datetime(2026, 10, 4, 7, tzinfo=timezone.utc)
        registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(), now=self.now)
        self.catalog = load_public_source_catalog(
            (fixtures / 'public-research-sources.json').read_bytes(), registry,
            now=self.now)
        self.empty = (fixtures / 'public-source-rights-evidence.json').read_bytes()
        self.record = ReviewedRightsEvidence(
            'REV_SYNTH2026100401', 'DOC_WATCH2026100301', 'NVDA',
            'internal_research', 'permitted',
            ('retrieve_once', 'extract_internal'),
            'https://example.test/synthetic-terms', 'a' * 64,
            self.now - timedelta(days=2), self.now - timedelta(days=1),
            self.now + timedelta(days=30), 'RVW_SYNTH2026100401', REVIEW_CHECKLIST)

    def record_payload(self, record=None):
        record = record or self.record
        return {
            'review_id': record.review_id, 'document_id': record.document_id,
            'symbol': record.symbol, 'use_case': record.use_case,
            'conclusion': record.conclusion,
            'permitted_actions': list(record.permitted_actions),
            'terms_uri': record.terms_uri,
            'evidence_sha256': record.evidence_sha256,
            'terms_observed_at': record.terms_observed_at.isoformat(),
            'reviewed_at': record.reviewed_at.isoformat(),
            'valid_until': record.valid_until.isoformat(),
            'reviewer_reference': record.reviewer_reference,
            'checklist_completed': list(record.checklist_completed),
        }

    def encode(self, records):
        return json.dumps({'schema_version': 1, 'records': records}).encode()

    def test_absent_real_evidence_blocks_all_candidates(self):
        records = load_reviewed_rights_evidence(
            self.empty, self.catalog, now=self.now)
        summary = assess_reviewed_rights(
            self.catalog, records, at=self.now).public_summary()
        self.assertEqual((summary['status'], summary['rights_allowed_count']),
                         ('blocked', 0))
        self.assertTrue(all(item['decision'] == 'missing_review_evidence'
                            for item in summary['items']))
        self.assertEqual(summary['technical_retrieval_status'],
                         'disabled_separate_gate')
        self.assertFalse(summary['release_authorized'])

    def test_complete_synthetic_reviews_can_pass_rights_only(self):
        records = []
        for index, candidate in enumerate(self.catalog.candidates, 1):
            record = replace(
                self.record, review_id=f'REV_SYNTH20261004{index:02d}',
                document_id=candidate.document_id, symbol=candidate.symbol,
                reviewer_reference=f'RVW_SYNTH20261004{index:02d}',
                evidence_sha256=str(index) * 64)
            records.append(self.record_payload(record))
        loaded = load_reviewed_rights_evidence(
            self.encode(records), self.catalog, now=self.now)
        summary = assess_reviewed_rights(
            self.catalog, loaded, at=self.now).public_summary()
        self.assertEqual((summary['status'], summary['rights_allowed_count']),
                         ('ready', 3))
        self.assertEqual(summary['technical_retrieval_status'],
                         'disabled_separate_gate')
        self.assertFalse(summary['release_authorized'])

    def test_prohibited_counsel_expired_and_missing_action_are_distinct(self):
        cases = (
            (replace(self.record, conclusion='prohibited', permitted_actions=()),
             'use_prohibited'),
            (replace(self.record, conclusion='needs_counsel', permitted_actions=()),
             'counsel_review_required'),
            (replace(self.record, valid_until=self.now), 'expired_review_evidence'),
            (replace(self.record, permitted_actions=('retrieve_once',)),
             'required_action_not_permitted'),
        )
        for record, code in cases:
            with self.subTest(code=code):
                report = assess_reviewed_rights(
                    self.catalog, [record], at=self.now)
                self.assertEqual(report.items[0].code, code)

    def test_manual_checklist_and_timing_are_required(self):
        variants = []
        payload = self.record_payload(); payload['checklist_completed'].pop(); variants.append(payload)
        payload = self.record_payload(); payload['reviewed_at'] = (self.now + timedelta(days=1)).isoformat(); variants.append(payload)
        payload = self.record_payload(); payload['terms_observed_at'] = self.now.isoformat(); variants.append(payload)
        payload = self.record_payload(); payload['valid_until'] = payload['reviewed_at']; variants.append(payload)
        for payload in variants:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                load_reviewed_rights_evidence(
                    self.encode([payload]), self.catalog, now=self.now)

    def test_schema_identity_actions_and_duplicate_reviews_fail_closed(self):
        variants = []
        payload = self.record_payload(); payload['document_id'] = 'DOC_UNKNOWN20261004'; variants.append([payload])
        payload = self.record_payload(); payload['permitted_actions'] = ['redistribute']; variants.append([payload])
        payload = self.record_payload(); payload['reviewer_reference'] = 'Alice'; variants.append([payload])
        payload = self.record_payload(); payload['extra'] = 'field'; variants.append([payload])
        variants.append([self.record_payload(), self.record_payload()])
        for records in variants:
            with self.subTest(records=records), self.assertRaises(ValueError):
                load_reviewed_rights_evidence(
                    self.encode(records), self.catalog, now=self.now)

    def test_same_time_conflict_is_ambiguous(self):
        conflict = replace(
            self.record, review_id='REV_SYNTH2026100499', conclusion='prohibited',
            permitted_actions=(), evidence_sha256='b' * 64)
        report = assess_reviewed_rights(
            self.catalog, [self.record, conflict], at=self.now)
        self.assertEqual(report.items[0].code, 'ambiguous_review_evidence')

    def test_invalid_bytes_and_operands_are_rejected(self):
        for raw in (b'', b'not-json', b'\xff', b'{' + b'x' * 262_144):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                load_reviewed_rights_evidence(raw, self.catalog, now=self.now)
        with self.assertRaisesRegex(ValueError, 'invalid_rights_evidence_assessment'):
            assess_reviewed_rights(self.catalog, [object()], at=self.now)
