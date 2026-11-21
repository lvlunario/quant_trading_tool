from dataclasses import replace
from datetime import date, datetime, timezone
import unittest

from atlas.weekly_research_report import (
    WeeklyResearchReport,
    WeeklyResearchSection,
    build_synthetic_weekly_research_report,
)


class WeeklyResearchReportTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 8, 11, 0, tzinfo=timezone.utc)
        self.report = build_synthetic_weekly_research_report(
            period_end=date(2026, 10, 8), generated_at=self.now)

    def test_report_has_exact_ordered_dated_sections(self):
        summary = self.report.public_summary()
        self.assertEqual(
            [item['section'] for item in summary['sections']],
            ['observation', 'hypothesis', 'counterargument', 'missing_evidence'])
        self.assertTrue(all(item['as_of'] == '2026-10-08'
                            for item in summary['sections']))
        self.assertEqual((summary['mode'], summary['status']),
                         ('synthetic', 'ready'))

    def test_sections_enforce_distinct_evidence_semantics(self):
        summary = self.report.public_summary()
        self.assertEqual(
            [(item['evidence_status'], item['source_status'])
             for item in summary['sections']],
            [('synthetic_verified', 'synthetic_fixture'),
             ('synthetic_assumption', 'not_applicable'),
             ('synthetic_assumption', 'not_applicable'),
             ('unavailable', 'missing')])

    def test_future_period_and_naive_generation_time_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'invalid_weekly_research_report'):
            replace(self.report, period_end=date(2026, 10, 9))
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_research_generated_at'):
            build_synthetic_weekly_research_report(
                generated_at=datetime(2026, 10, 8, 11, 0))

    def test_missing_duplicate_or_reordered_sections_fail_closed(self):
        for sections in (
                self.report.sections[:-1],
                self.report.sections[:3] + (self.report.sections[2],),
                tuple(reversed(self.report.sections))):
            with self.subTest(sections=sections):
                with self.assertRaisesRegex(
                        ValueError, 'invalid_weekly_research_report'):
                    WeeklyResearchReport(
                        self.report.period_end, self.report.generated_at, sections)

    def test_evidence_promotion_outside_section_semantics_is_rejected(self):
        hypothesis = self.report.sections[1]
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_research_section'):
            WeeklyResearchSection(
                hypothesis.statement_id, hypothesis.section, hypothesis.text,
                hypothesis.as_of, 'synthetic_verified', 'synthetic_fixture')


if __name__ == '__main__':
    unittest.main()
