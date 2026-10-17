from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import unittest

from atlas.provider_qualification import (
    ProviderQualificationEvidence,
    assess_provider_qualification,
    default_provider_qualification_policy,
)


class ProviderQualificationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 30, 7, tzinfo=timezone.utc)
        self.policy = default_provider_qualification_policy()
        self.evidence = ProviderQualificationEvidence(
            'QEV_PROVIDERQUAL01', 'private_authorized', self.policy.provider_id,
            self.policy.dataset_id, self.policy.extractor_version,
            'BOUND_PRIVATE01', 'AUTH_PROVIDER01', 'a' * 64, 'b' * 64,
            ('REV_PRIMARY01', 'REV_INDEPENDENT02'), ('v1_json', 'v2_json'),
            ('v1_json', 'v2_json'), 30, 200, 198, 0, 0,
            self.now - timedelta(days=1), self.now + timedelta(days=30))

    def assess(self, evidence=None):
        return assess_provider_qualification(
            self.policy, self.evidence if evidence is None else evidence,
            now=self.now)

    def test_complete_private_evidence_meets_technical_gate_only(self):
        report = self.assess()
        self.assertEqual(report['status'], 'qualified_private')
        self.assertEqual(report['codes'], ['private_provider_qualified'])
        self.assertEqual(report['exact_match_rate'], '0.99')
        self.assertEqual(report['format_coverage_rate'], '1')
        self.assertFalse(report['release_authorized'])

    def test_absent_external_evidence_blocks_with_safe_requirements(self):
        report = assess_provider_qualification(self.policy, now=self.now)
        self.assertEqual(report['status'], 'blocked')
        self.assertIn('private_boundary_evidence_missing', report['codes'])
        self.assertIn('measured_quality_missing', report['codes'])
        self.assertEqual(report['evidence_scope'], 'none')

    def test_synthetic_evidence_cannot_qualify_real_provider(self):
        report = self.assess(replace(self.evidence, scope='synthetic'))
        self.assertEqual(report['status'], 'blocked')
        self.assertIn('synthetic_evidence_only', report['codes'])

    def test_identity_or_extractor_drift_blocks(self):
        evidence = replace(
            self.evidence, provider_id='PRV_OTHER1234',
            dataset_id='DATA_OTHER1234', extractor_version='atlas.other@1.0.0')
        report = self.assess(evidence)
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['codes'][:3], [
            'provider_identity_mismatch', 'dataset_identity_mismatch',
            'extractor_version_mismatch'])

    def test_sample_quality_and_format_thresholds_fail_closed(self):
        evidence = replace(
            self.evidence, document_count=29, field_check_count=199,
            exact_match_count=190, tested_formats=('v1_json',),
            critical_error_count=1, semantic_mismatch_count=1)
        report = self.assess(evidence)
        for code in (
            'insufficient_document_count', 'insufficient_field_check_count',
            'exact_match_rate_below_threshold', 'format_coverage_incomplete',
            'critical_error_limit_exceeded', 'semantic_mismatch_limit_exceeded',
        ):
            self.assertIn(code, report['codes'])

    def test_stale_or_future_evaluation_blocks(self):
        expired = replace(
            self.evidence, evaluated_at=self.now - timedelta(days=3),
            expires_at=self.now - timedelta(days=1))
        self.assertIn('qualification_evidence_expired', self.assess(expired)['codes'])
        future = replace(
            self.evidence, evaluated_at=self.now + timedelta(days=1),
            expires_at=self.now + timedelta(days=2))
        self.assertIn('qualification_evaluation_in_future',
                      self.assess(future)['codes'])

    def test_structurally_invalid_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_provider_qualification_evidence'):
            replace(self.evidence, exact_match_count=201)
        with self.assertRaisesRegex(ValueError,
                                    'invalid_provider_qualification_evidence'):
            replace(self.evidence, reviewer_ids=('REV_DUPLICATE01',
                                                 'REV_DUPLICATE01'))

    def test_report_redacts_evidence_identifiers_and_hashes(self):
        encoded = json.dumps(self.assess())
        for private_value in (
            self.evidence.evidence_id, self.evidence.corpus_digest,
            self.evidence.label_set_digest, self.evidence.authorization_receipt_id,
            self.evidence.private_boundary_receipt_id,
            *self.evidence.reviewer_ids,
        ):
            self.assertNotIn(private_value, encoded)


if __name__ == '__main__':
    unittest.main()
