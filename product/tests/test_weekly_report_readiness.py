from dataclasses import replace
from datetime import date, datetime, timezone
import unittest

from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.weekly_report_readiness import (
    WeeklyReportReadiness, assess_weekly_report_readiness,
)
from atlas.weekly_research_report import build_synthetic_weekly_research_report


class WeeklyReportReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 9, 7, 0, tzinfo=timezone.utc)
        self.report = build_synthetic_weekly_research_report(
            period_end=date(2026, 10, 9), generated_at=self.now)
        names = ('identity', 'source_discovery', 'rights_review',
                 'capture_authorization', 'extraction', 'metric_release')
        counts = (8, 8, 0, 0, 0, 0)
        blockers = ('identity_unresolved', 'source_candidate_missing',
                    'rights_review_incomplete',
                    'capture_authorization_incomplete',
                    'no_authorized_source_bytes',
                    'no_verified_metric_evidence')
        stages = tuple(M2GateStage(name, count, 9 - count, blocker)
                       for name, count, blocker in zip(names, counts, blockers))
        self.trace = M2AcceptanceTrace(self.now, 9, stages)

    def test_summary_separates_ready_shell_from_blocked_sourced_report(self):
        summary = assess_weekly_report_readiness(
            self.report, self.trace).public_summary()
        self.assertEqual(summary['status'], 'blocked_sourced_report')
        self.assertEqual(summary['synthetic_shell'], {
            'status': 'ready', 'section_count': 4,
            'claim_types_separated': True,
        })
        self.assertEqual(summary['sourced_report']['stage_passed_counts'],
                         [8, 8, 0, 0, 0, 0])
        self.assertEqual((summary['sourced_report']['sourced_statement_count'],
                          summary['sourced_report']['sourced_metric_count']),
                         (0, 0))

    def test_readiness_records_no_conclusion_acceptance_or_release(self):
        summary = assess_weekly_report_readiness(
            self.report, self.trace).public_summary()
        self.assertFalse(summary['investment_conclusion'])
        self.assertFalse(summary['milestone_acceptance_recorded'])
        self.assertFalse(summary['release_authorized'])

    def test_mismatched_assessment_time_or_wrong_type_fails_closed(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_report_readiness_input'):
            assess_weekly_report_readiness(
                self.report, replace(
                    self.trace,
                    assessed_at=datetime(2026, 10, 9, 8, 0,
                                         tzinfo=timezone.utc)))
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_report_readiness_input'):
            assess_weekly_report_readiness({}, self.trace)

    def test_nonzero_sourced_extraction_or_metric_is_not_promoted(self):
        counts = (8, 8, 1, 1, 1, 1)
        stages = tuple(replace(stage, passed_count=count,
                               blocked_count=9 - count)
                       for stage, count in zip(self.trace.stages, counts))
        with self.assertRaisesRegex(ValueError,
                                    'sourced_weekly_evidence_not_supported'):
            assess_weekly_report_readiness(
                self.report, replace(self.trace, stages=stages))

    def test_invalid_public_model_counts_fail_closed(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_report_readiness'):
            WeeklyReportReadiness(
                self.now, self.now.date(), 4, 9,
                (8, 8, 0, 0, 1, 0),
                tuple(stage.blocker for stage in self.trace.stages))


if __name__ == '__main__':
    unittest.main()
