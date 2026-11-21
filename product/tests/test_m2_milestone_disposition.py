from dataclasses import replace
from datetime import datetime, timezone
import json
import unittest

from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.m2_milestone_disposition import (
    M2MilestoneDisposition,
    recommend_m2_milestone_disposition,
)
from atlas.m2_milestone_readiness import assess_m2_milestone_readiness
from atlas.weekly_publication_decision import WeeklyPublicationDecision


class M2MilestoneDispositionTests(unittest.TestCase):
    def setUp(self):
        self.at = datetime(2026, 10, 12, 11, 0, tzinfo=timezone.utc)
        names = ('identity', 'source_discovery', 'rights_review',
                 'capture_authorization', 'extraction', 'metric_release')
        counts = (8, 8, 0, 0, 0, 0)
        trace = M2AcceptanceTrace(
            self.at, 9,
            tuple(M2GateStage(name, count, 9 - count, f'{name}_blocked')
                  for name, count in zip(names, counts)))
        publication = WeeklyPublicationDecision(
            self.at, self.at.date(), 9, counts, 23, 13, 10, 1, 3)
        conformance = {
            'status': 'passed',
            'assessed_at': self.at.isoformat(),
            'synthetic_scenario': {
                'stages': [{'gate': name, 'status': 'passed'}
                           for name in names],
            },
            'public_source_state': {'passed_counts': list(counts)},
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
        }
        self.readiness = assess_m2_milestone_readiness(
            trace, publication, conformance)

    def test_unresolved_criteria_become_explicit_deferrals(self):
        summary = recommend_m2_milestone_disposition(
            self.readiness).public_summary()
        self.assertEqual((summary['status'], summary['receipt_state']),
                         ('blocked', 'candidate'))
        self.assertEqual(summary['deferred_count'], 6)
        self.assertEqual(summary['review_recommended_count'], 0)
        self.assertTrue(all(item['recommendation'] == 'recommend_defer'
                            for item in summary['criteria']))
        self.assertEqual(summary['overall_recommendation'],
                         'defer_unresolved_criteria')

    def test_completed_criteria_are_reviewable_not_accepted(self):
        readiness = replace(
            self.readiness, public_passed_counts=(9, 9, 0, 0, 0, 0))
        summary = recommend_m2_milestone_disposition(
            readiness).public_summary()
        self.assertEqual(
            [item['recommendation'] for item in summary['criteria'][:2]],
            ['recommend_review', 'recommend_review'])
        self.assertEqual([item['blocker'] for item in summary['criteria'][:2]],
                         ['none', 'none'])
        self.assertEqual((summary['review_recommended_count'],
                          summary['deferred_count']), (2, 4))
        self.assertFalse(summary['founder_response_recorded'])
        self.assertFalse(summary['milestone_acceptance_recorded'])

    def test_checkpoint_state_is_derived_from_assessment_date(self):
        summary = recommend_m2_milestone_disposition(
            self.readiness).public_summary()
        self.assertEqual((summary['checkpoint_date'],
                          summary['checkpoint_status']),
                         ('2026-10-17', 'scheduled'))

    def test_manila_midnight_controls_checkpoint_and_readiness(self):
        cases = (
            ('2026-10-16T15:59:59+00:00', 'scheduled', 1, 'active'),
            ('2026-10-16T16:00:00+00:00', 'due', 0, 'active'),
            ('2026-10-17T15:59:59+00:00', 'due', 0, 'active'),
            ('2026-10-17T16:00:00+00:00', 'elapsed', -1, 'elapsed'),
            ('2026-10-17T00:00:00+08:00', 'due', 0, 'active'),
        )
        for timestamp, status, days, target_status in cases:
            with self.subTest(timestamp=timestamp):
                readiness = replace(self.readiness,
                                    assessed_at=datetime.fromisoformat(timestamp))
                summary = recommend_m2_milestone_disposition(
                    readiness).public_summary()
                self.assertEqual(summary['checkpoint_status'], status)
                self.assertEqual(readiness.public_summary()['days_to_target'], days)
                self.assertEqual(readiness.public_summary()['target_status'],
                                 target_status)
                self.assertEqual(summary['deferred_count'], 6)
                self.assertFalse(summary['milestone_acceptance_recorded'])

    def test_invalid_readiness_input_fails_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'invalid_m2_milestone_disposition_input'):
            recommend_m2_milestone_disposition({})
        disposition = recommend_m2_milestone_disposition(self.readiness)
        with self.assertRaisesRegex(
                ValueError, 'invalid_m2_milestone_disposition'):
            replace(disposition, publication_decision='publish')

    def test_public_receipt_excludes_private_and_authority_fields(self):
        encoded = json.dumps(recommend_m2_milestone_disposition(
            self.readiness).public_summary())
        for excluded in ('source_uri', 'document_id', 'review_id',
                         'evidence_sha256', 'metric_value',
                         'reviewer_reference', 'approval_id'):
            self.assertNotIn(excluded, encoded)
        self.assertIn('"release_authorized": false', encoded)


if __name__ == '__main__':
    unittest.main()
