from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from atlas.extraction_quality import ExtractionEvidence, assess_extraction_quality
from atlas.metric_evidence import MetricPayload
from atlas.metrics import MetricDefinition, MetricValue
from atlas.source_evidence import ResearchSourceRecord


class ExtractionQualityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        self.source = ResearchSourceRecord(
            'DOC_123456789ABC', 'INS_123456789ABC', 'PRV_12345678',
            'DATA_12345678', 'licensed_dataset', 'application/json',
            self.now - timedelta(days=2), self.now - timedelta(days=1),
            self.now - timedelta(hours=1), 'https://example.test/source', 'a' * 64)
        definition = MetricDefinition(
            'MET_REVENUE', '1.0.0', 'Reported revenue', 'money', 'USD',
            'quarter', 'missing', 'reported@1.0.0')
        self.payload = MetricPayload(
            MetricValue(definition, Decimal('123.40')),
            date(2026, 4, 1), date(2026, 6, 30))
        self.evidence = ExtractionEvidence(
            'EXT_123456789ABC', self.source.document_id, definition.metric_id,
            self.source.source_sha256, self.payload.payload_sha256,
            'deterministic_parser', 'atlas.json@1.0.0', self.source.retrieved_at,
            'not_required', None)

    def assess(self, evidence=None):
        return assess_extraction_quality(
            evidence or self.evidence, self.source, self.payload, now=self.now)

    def test_deterministic_exact_binding_is_ready(self):
        result = self.assess()
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.codes, ('deterministic_extraction_verified',))

    def test_manual_or_assisted_extraction_requires_verified_review(self):
        for method in ('manual_entry', 'llm_assisted'):
            with self.subTest(method=method):
                unverified = replace(self.evidence, method=method,
                                     review_status='unverified')
                self.assertEqual(self.assess(unverified).codes,
                                 ('extraction_review_required',))
                verified = replace(
                    unverified, review_status='verified',
                    reviewer_evidence_sha256='b' * 64)
                self.assertEqual(self.assess(verified).status, 'ready')

    def test_rejected_review_cannot_release_extraction(self):
        rejected = replace(
            self.evidence, review_status='rejected',
            reviewer_evidence_sha256='b' * 64)
        self.assertEqual(self.assess(rejected).codes, ('extraction_rejected',))

    def test_exact_source_metric_and_payload_bindings_are_required(self):
        cases = (
            ('document_id', 'DOC_ABCDEFGHIJKL', 'extraction_document_mismatch'),
            ('source_sha256', 'b' * 64, 'extraction_source_hash_mismatch'),
            ('metric_id', 'MET_OTHER', 'extraction_metric_mismatch'),
            ('payload_sha256', 'b' * 64, 'extraction_payload_hash_mismatch'),
        )
        for field, value, code in cases:
            with self.subTest(code=code):
                self.assertIn(code, self.assess(replace(
                    self.evidence, **{field: value})).codes)

    def test_timing_and_contract_semantics_fail_closed(self):
        self.assertIn('extraction_before_retrieval', self.assess(replace(
            self.evidence,
            extracted_at=self.source.retrieved_at - timedelta(seconds=1))).codes)
        self.assertIn('extraction_in_future', self.assess(replace(
            self.evidence, extracted_at=self.now + timedelta(seconds=1))).codes)
        with self.assertRaises(ValueError):
            replace(self.evidence, method='manual_entry')
        with self.assertRaises(ValueError):
            replace(self.evidence, extraction_id='bad')
        with self.assertRaises(ValueError):
            replace(self.evidence, reviewer_evidence_sha256='bad')


if __name__ == '__main__':
    unittest.main()
