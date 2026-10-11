"""Fail-closed publication decision for the weekly research boundary."""
from dataclasses import dataclass
from datetime import date, datetime

from .weekly_claim_receipt import WeeklyClaimEvidenceReceipt
from .weekly_report_readiness import WeeklyReportReadiness


@dataclass(frozen=True)
class WeeklyPublicationDecision:
    assessed_at: datetime
    period_end: date
    universe_count: int
    sourced_passed_counts: tuple[int, ...]
    required_field_count: int
    provided_field_count: int
    missing_field_count: int
    synthetic_field_complete_count: int
    blocked_claim_count: int

    def __post_init__(self):
        counts = self.sourced_passed_counts
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                not isinstance(self.period_end, date) or
                self.period_end > self.assessed_at.date() or
                self.universe_count != 9 or
                len(counts) != 6 or
                any(not isinstance(count, int) or isinstance(count, bool) or
                    not 0 <= count <= self.universe_count for count in counts) or
                any(later > earlier
                    for earlier, later in zip(counts, counts[1:])) or
                counts[-2:] != (0, 0) or
                self.required_field_count != 23 or
                not 0 <= self.provided_field_count <= 23 or
                self.missing_field_count !=
                self.required_field_count - self.provided_field_count or
                not 0 <= self.synthetic_field_complete_count <= 4 or
                self.blocked_claim_count !=
                4 - self.synthetic_field_complete_count):
            raise ValueError('invalid_weekly_publication_decision')

    def public_summary(self):
        bindings_complete = self.missing_field_count == 0
        return {
            'schema_version': 1,
            'status': 'blocked',
            'decision': 'withhold_publication',
            'assessed_at': self.assessed_at.isoformat(),
            'period_end': self.period_end.isoformat(),
            'sourced_report': {
                'status': 'blocked',
                'universe_count': self.universe_count,
                'stage_passed_counts': list(self.sourced_passed_counts),
                'sourced_statement_count': 0,
                'sourced_metric_count': 0,
            },
            'claim_bindings': {
                'status': ('synthetic_fields_complete_not_evidence'
                           if bindings_complete
                           else 'blocked_missing_bindings'),
                'required_field_count': self.required_field_count,
                'provided_field_count': self.provided_field_count,
                'missing_field_count': self.missing_field_count,
                'synthetic_field_complete_count':
                    self.synthetic_field_complete_count,
                'blocked_claim_count': self.blocked_claim_count,
                'evidence_values_status': 'not_accepted',
            },
            'publication_gate': {
                'status': 'blocked',
                'primary_blocker': 'sourced_evidence_not_available',
                'synthetic_presence_can_authorize': False,
            },
            'actual_report_eligible': False,
            'investment_conclusion': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'readiness': ('withhold publication until permitted sourced '
                          'statements and metrics pass every independent gate'),
        }


def assess_weekly_publication_decision(readiness, receipt):
    """Compose public-safe counts; synthetic presence never grants release."""
    if (not isinstance(readiness, WeeklyReportReadiness) or
            not isinstance(receipt, WeeklyClaimEvidenceReceipt) or
            readiness.assessed_at != receipt.assessed_at):
        raise ValueError('invalid_weekly_publication_decision_input')
    required = sum(len(rule.required_fields)
                   for rule in receipt.manifest.rules)
    provided = sum(len(binding.provided_fields)
                   for binding in receipt.bindings)
    complete = sum(
        len(binding.provided_fields) == len(rule.required_fields)
        for rule, binding in zip(receipt.manifest.rules, receipt.bindings)
    )
    return WeeklyPublicationDecision(
        readiness.assessed_at,
        readiness.period_end,
        readiness.universe_count,
        readiness.sourced_passed_counts,
        required,
        provided,
        required - provided,
        complete,
        len(receipt.bindings) - complete,
    )
