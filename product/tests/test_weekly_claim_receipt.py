from dataclasses import replace
from datetime import datetime, timezone
import json
import unittest

from atlas.weekly_claim_receipt import (
    SyntheticClaimBinding,
    WeeklyClaimEvidenceReceipt,
    build_synthetic_weekly_claim_evidence_receipt,
)


class WeeklyClaimReceiptTests(unittest.TestCase):
    def setUp(self):
        self.at = datetime(2026, 10, 10, 7, 0, tzinfo=timezone.utc)
        self.receipt = build_synthetic_weekly_claim_evidence_receipt(
            assessed_at=self.at)

    def test_fixed_receipt_counts_present_and_missing_fields(self):
        summary = self.receipt.public_summary()
        self.assertEqual(
            (summary['required_field_count'], summary['provided_field_count'],
             summary['missing_field_count']),
            (23, 13, 10))
        self.assertEqual(
            [(item['required_field_count'], item['provided_field_count'])
             for item in summary['sections']],
            [(8, 8), (5, 3), (5, 2), (5, 0)])
        self.assertEqual(summary['synthetic_field_complete_count'], 1)
        self.assertEqual(summary['blocked_claim_count'], 3)

    def test_public_summary_excludes_field_names_and_evidence_values(self):
        encoded = json.dumps(self.receipt.public_summary())
        for excluded in (
                'claim_id', 'instrument_id', 'source_document_id',
                'observation_id', 'rights_decision', 'available_at',
                'extraction_quality', 'supporting_claim_ids'):
            self.assertNotIn(excluded, encoded)
        self.assertEqual(
            self.receipt.public_summary()['evidence_values_status'],
            'not_accepted')

    def test_unknown_duplicate_or_reordered_field_fails_closed(self):
        manifest = self.receipt.manifest
        for fields in (
                ('unknown_field',),
                ('claim_id', 'claim_id'),
                ('as_of', 'claim_id')):
            with self.assertRaisesRegex(
                    ValueError, 'invalid_synthetic_claim_binding'):
                SyntheticClaimBinding(
                    'observation', fields).validate_against(manifest)

    def test_receipt_rejects_wrong_order_cutoff_or_binding_type(self):
        bindings = self.receipt.bindings
        for change in (
                {'bindings': tuple(reversed(bindings))},
                {'assessed_at': datetime(2026, 10, 10, 7, 0)},
                {'bindings': bindings[:-1] + ('not-a-binding',)}):
            with self.assertRaisesRegex(ValueError,
                                        'invalid_weekly_claim_receipt'):
                replace(self.receipt, **change)

    def test_structural_completeness_never_grants_actual_eligibility(self):
        summary = self.receipt.public_summary()
        self.assertEqual(summary['status'], 'blocked')
        self.assertFalse(summary['actual_report_eligible'])
        self.assertFalse(summary['investment_conclusion'])
        self.assertFalse(summary['milestone_acceptance_recorded'])
        self.assertFalse(summary['release_authorized'])


if __name__ == '__main__':
    unittest.main()
