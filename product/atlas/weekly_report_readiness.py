"""Public-safe readiness boundary for synthetic versus sourced weekly reports."""
from dataclasses import dataclass
from datetime import date, datetime

from .m2_acceptance_trace import M2AcceptanceTrace
from .weekly_research_report import WeeklyResearchReport


@dataclass(frozen=True)
class WeeklyReportReadiness:
    assessed_at: datetime
    period_end: date
    synthetic_section_count: int
    universe_count: int
    sourced_passed_counts: tuple[int, ...]
    sourced_blockers: tuple[str, ...]

    def __post_init__(self):
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                not isinstance(self.period_end, date) or
                self.period_end > self.assessed_at.date() or
                self.synthetic_section_count != 4 or
                self.universe_count != 9 or
                len(self.sourced_passed_counts) != 6 or
                len(self.sourced_blockers) != 6 or
                any(not isinstance(count, int) or isinstance(count, bool) or
                    not 0 <= count <= self.universe_count
                    for count in self.sourced_passed_counts) or
                any(not blocker for blocker in self.sourced_blockers) or
                self.sourced_passed_counts[-2:] != (0, 0)):
            raise ValueError('invalid_weekly_report_readiness')

    def public_summary(self):
        return {
            'schema_version': 1,
            'status': 'blocked_sourced_report',
            'assessed_at': self.assessed_at.isoformat(),
            'period_end': self.period_end.isoformat(),
            'synthetic_shell': {
                'status': 'ready',
                'section_count': self.synthetic_section_count,
                'claim_types_separated': True,
            },
            'sourced_report': {
                'status': 'blocked',
                'universe_count': self.universe_count,
                'stage_passed_counts': list(self.sourced_passed_counts),
                'stage_blockers': list(self.sourced_blockers),
                'sourced_statement_count': 0,
                'sourced_metric_count': 0,
            },
            'investment_conclusion': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'readiness': ('synthetic report structure is visible; sourced weekly '
                          'research remains blocked before extraction and metric '
                          'release'),
        }


def assess_weekly_report_readiness(report, trace):
    """Compose structural readiness without promoting missing source evidence."""
    if (not isinstance(report, WeeklyResearchReport) or
            not isinstance(trace, M2AcceptanceTrace) or
            report.generated_at != trace.assessed_at or
            report.period_end != report.generated_at.date()):
        raise ValueError('invalid_weekly_report_readiness_input')
    counts = tuple(stage.passed_count for stage in trace.stages)
    blockers = tuple(stage.blocker for stage in trace.stages)
    if counts[-2:] != (0, 0):
        raise ValueError('sourced_weekly_evidence_not_supported')
    return WeeklyReportReadiness(
        trace.assessed_at, report.period_end, len(report.sections),
        trace.universe_count, counts, blockers)
