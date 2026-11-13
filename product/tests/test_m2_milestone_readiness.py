from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timezone
import json
import unittest

from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.m2_milestone_readiness import assess_m2_milestone_readiness
from atlas.weekly_publication_decision import WeeklyPublicationDecision


class M2MilestoneReadinessTests(unittest.TestCase):
    def setUp(self):
        self.at = datetime(2026, 10, 11, 11, 0, tzinfo=timezone.utc)
        names = ('identity', 'source_discovery', 'rights_review',
                 'capture_authorization', 'extraction', 'metric_release')
        counts = (8, 8, 0, 0, 0, 0)
        self.trace = M2AcceptanceTrace(
            self.at, 9,
            tuple(M2GateStage(name, count, 9 - count, f'{name}_blocked')
                  for name, count in zip(names, counts)))
        self.publication = WeeklyPublicationDecision(
            self.at, self.at.date(), 9, counts, 23, 13, 10, 1, 3)
        self.conformance = {
            'status': 'passed',
            'assessed_at': self.at.isoformat(),
            'synthetic_scenario': {
                'stages': [{'gate': name, 'status': 'passed'} for name in names],
            },
            'public_source_state': {'passed_counts': list(counts)},
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
        }
        self.readiness = assess_m2_milestone_readiness(
            self.trace, self.publication, self.conformance)

    def test_current_m2_state_separates_synthetic_and_sourced_readiness(self):
        summary = self.readiness.public_summary()
        self.assertEqual((summary['status'], summary['target_date']),
                         ('blocked', '2026-10-17'))
        self.assertEqual(summary['synthetic_controls']['technical_gates_passed'],
                         6)
        self.assertEqual(
            [item['passed_count'] for item in summary['sourced_exit_criteria']],
            [8, 8, 0, 0, 0, 0])
        self.assertEqual(summary['weekly_publication']['decision'],
                         'withhold_publication')
        self.assertFalse(summary['milestone_acceptance_recorded'])
        self.assertFalse(summary['release_authorized'])

    def test_public_summary_lists_controlled_dependencies_only(self):
        encoded = json.dumps(self.readiness.public_summary())
        self.assertEqual(len(self.readiness.public_summary()
                             ['external_dependencies']), 5)
        for excluded in ('source_uri', 'document_id', 'review_id',
                         'evidence_sha256', 'metric_value', 'reviewer_reference'):
            self.assertNotIn(excluded, encoded)

    def test_misaligned_or_weakened_evidence_fails_closed(self):
        cases = []
        changed_time = deepcopy(self.conformance)
        changed_time['assessed_at'] = datetime(
            2026, 10, 11, 11, 1, tzinfo=timezone.utc).isoformat()
        cases.append(changed_time)
        failed_gate = deepcopy(self.conformance)
        failed_gate['synthetic_scenario']['stages'][-1]['status'] = 'blocked'
        cases.append(failed_gate)
        changed_public = deepcopy(self.conformance)
        changed_public['public_source_state']['passed_counts'][-1] = 1
        cases.append(changed_public)
        for conformance in cases:
            with self.assertRaisesRegex(
                    ValueError, 'invalid_m2_milestone_readiness_input'):
                assess_m2_milestone_readiness(
                    self.trace, self.publication, conformance)

    def test_invalid_milestone_counts_fail_closed(self):
        for change in (
                {'target_date': date(2026, 10, 18)},
                {'public_passed_counts': (8, 8, 0, 0, 1, 0)},
                {'publication_decision': 'publish'},
                {'provided_field_count': 14}):
            with self.assertRaisesRegex(
                    ValueError, 'invalid_m2_milestone_readiness'):
                replace(self.readiness, **change)


if __name__ == '__main__':
    unittest.main()
