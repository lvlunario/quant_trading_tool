from dataclasses import replace
from datetime import datetime, timezone
import json
import unittest

from atlas.weekly_claim_receipt import (
    SyntheticClaimBinding,
    WeeklyClaimEvidenceReceipt,
    build_synthetic_weekly_claim_evidence_receipt,
)
from atlas.weekly_publication_decision import (
    assess_weekly_publication_decision,
)
from atlas.weekly_report_readiness import WeeklyReportReadiness


class WeeklyPublicationDecisionTests(unittest.TestCase):
    def setUp(self):
        self.at = datetime(2026, 10, 11, 0, 0, tzinfo=timezone.utc)
        self.readiness = WeeklyReportReadiness(
            self.at, self.at.date(), 4, 9, (8, 8, 0, 0, 0, 0),
            ('identity_unresolved', 'source_candidate_missing',
             'rights_review_incomplete', 'capture_not_authorized',
             'extraction_not_complete', 'metric_release_not_ready'))
        self.receipt = build_synthetic_weekly_claim_evidence_receipt(
            assessed_at=self.at)
        self.decision = assess_weekly_publication_decision(
            self.readiness, self.receipt)

    def test_current_boundary_withholds_publication(self):
        summary = self.decision.public_summary()
        self.assertEqual(
            (summary['status'], summary['decision']),
            ('blocked', 'withhold_publication'))
        self.assertEqual(
            summary['sourced_report']['stage_passed_counts'],
            [8, 8, 0, 0, 0, 0])
        self.assertEqual(
            (summary['claim_bindings']['required_field_count'],
             summary['claim_bindings']['provided_field_count'],
             summary['claim_bindings']['missing_field_count']),
            (23, 13, 10))

    def test_synthetic_completeness_cannot_authorize_publication(self):
        manifest = self.receipt.manifest
        complete_receipt = WeeklyClaimEvidenceReceipt(
            self.at, manifest,
            tuple(SyntheticClaimBinding(rule.section, rule.required_fields)
                  for rule in manifest.rules))
        summary = assess_weekly_publication_decision(
            self.readiness, complete_receipt).public_summary()
        self.assertEqual(
            summary['claim_bindings']['status'],
            'synthetic_fields_complete_not_evidence')
        self.assertEqual(summary['claim_bindings']['missing_field_count'], 0)
        self.assertFalse(
            summary['publication_gate']['synthetic_presence_can_authorize'])
        self.assertFalse(summary['actual_report_eligible'])
        self.assertFalse(summary['release_authorized'])

    def test_public_summary_is_count_only(self):
        encoded = json.dumps(self.decision.public_summary())
        for excluded in (
                'claim_id', 'instrument_id', 'source_document_id',
                'observation_id', 'rights_decision', 'supporting_claim_ids',
                'source_uri', 'sha256', 'metric_value'):
            self.assertNotIn(excluded, encoded)
        self.assertEqual(
            self.decision.public_summary()['claim_bindings']
            ['evidence_values_status'], 'not_accepted')

    def test_misaligned_or_wrong_inputs_fail_closed(self):
        later_receipt = build_synthetic_weekly_claim_evidence_receipt(
            assessed_at=datetime(2026, 10, 11, 0, 1, tzinfo=timezone.utc))
        for readiness, receipt in (
                ('not-readiness', self.receipt),
                (self.readiness, 'not-receipt'),
                (self.readiness, later_receipt)):
            with self.assertRaisesRegex(
                    ValueError, 'invalid_weekly_publication_decision_input'):
                assess_weekly_publication_decision(readiness, receipt)

    def test_invalid_counts_and_progression_fail_closed(self):
        for change in (
                {'sourced_passed_counts': (8, 9, 0, 0, 0, 0)},
                {'sourced_passed_counts': (8, 8, 0, 0, 1, 0)},
                {'provided_field_count': 14},
                {'blocked_claim_count': 4}):
            with self.assertRaisesRegex(
                    ValueError, 'invalid_weekly_publication_decision'):
                replace(self.decision, **change)


if __name__ == '__main__':
    unittest.main()
