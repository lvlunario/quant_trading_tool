"""Public-safe M2 milestone readiness; never records acceptance."""
from dataclasses import dataclass
from datetime import date, datetime

from .m2_acceptance_trace import M2AcceptanceTrace
from .weekly_publication_decision import WeeklyPublicationDecision


M2_TARGET_DATE = date(2026, 10, 17)


@dataclass(frozen=True)
class M2MilestoneReadiness:
    assessed_at: datetime
    target_date: date
    universe_count: int
    public_passed_counts: tuple[int, ...]
    synthetic_gate_count: int
    publication_decision: str
    required_field_count: int
    provided_field_count: int
    missing_field_count: int

    def __post_init__(self):
        counts = self.public_passed_counts
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.target_date != M2_TARGET_DATE or
                self.universe_count != 9 or
                len(counts) != 6 or
                any(not isinstance(count, int) or isinstance(count, bool) or
                    not 0 <= count <= self.universe_count for count in counts) or
                any(later > earlier
                    for earlier, later in zip(counts, counts[1:])) or
                counts[-2:] != (0, 0) or
                self.synthetic_gate_count != 6 or
                self.publication_decision != 'withhold_publication' or
                self.required_field_count != 23 or
                not 0 <= self.provided_field_count <= 23 or
                self.missing_field_count !=
                self.required_field_count - self.provided_field_count):
            raise ValueError('invalid_m2_milestone_readiness')

    def public_summary(self):
        days_to_target = (self.target_date - self.assessed_at.date()).days
        criteria = (
            ('identity', self.public_passed_counts[0], 9,
             'identity_unresolved'),
            ('source_discovery', self.public_passed_counts[1], 9,
             'source_candidate_missing'),
            ('rights_review', self.public_passed_counts[2], 8,
             'rights_review_incomplete'),
            ('capture_authorization', self.public_passed_counts[3], 8,
             'capture_authorization_incomplete'),
            ('extraction', self.public_passed_counts[4], 9,
             'no_authorized_source_bytes'),
            ('metric_release', self.public_passed_counts[5], 9,
             'no_verified_metric_evidence'),
        )
        return {
            'schema_version': 1,
            'status': 'blocked',
            'phase': 'M2 Sourced Research',
            'assessed_at': self.assessed_at.isoformat(),
            'target_date': self.target_date.isoformat(),
            'target_status': 'active' if days_to_target >= 0 else 'elapsed',
            'days_to_target': days_to_target,
            'synthetic_controls': {
                'status': 'ready_for_review',
                'technical_gate_count': self.synthetic_gate_count,
                'technical_gates_passed': self.synthetic_gate_count,
                'uses_invented_fixture_only': True,
            },
            'sourced_exit_criteria': [
                {
                    'criterion': name,
                    'status': 'ready' if passed == required else 'blocked',
                    'passed_count': passed,
                    'required_count': required,
                    'blocker': blocker,
                }
                for name, passed, required, blocker in criteria
            ],
            'weekly_publication': {
                'decision': self.publication_decision,
                'required_field_count': self.required_field_count,
                'provided_field_count': self.provided_field_count,
                'missing_field_count': self.missing_field_count,
                'sourced_statement_count': 0,
                'sourced_metric_count': 0,
            },
            'external_dependencies': [
                'crbs_identity_resolution',
                'completed_rights_review',
                'technical_capture_approval',
                'permitted_exact_source_evidence',
                'licensed_metric_data',
            ],
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'recommendation': ('continue synthetic review preparation; do not '
                               'claim sourced M2 completion'),
        }


def assess_m2_milestone_readiness(trace, publication, conformance):
    """Compose verified synthetic proof with the independently blocked path."""
    if (not isinstance(trace, M2AcceptanceTrace) or
            not isinstance(publication, WeeklyPublicationDecision) or
            not isinstance(conformance, dict)):
        raise ValueError('invalid_m2_milestone_readiness_input')
    try:
        conformance_at = datetime.fromisoformat(conformance['assessed_at'])
        synthetic_stages = conformance['synthetic_scenario']['stages']
        public_counts = tuple(
            conformance['public_source_state']['passed_counts'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('invalid_m2_milestone_readiness_input') from None
    trace_counts = tuple(stage.passed_count for stage in trace.stages)
    publication_summary = publication.public_summary()
    if (publication.assessed_at != trace.assessed_at or
            conformance_at != trace.assessed_at or
            conformance.get('status') != 'passed' or
            len(synthetic_stages) != 6 or
            any(stage.get('status') != 'passed'
                for stage in synthetic_stages) or
            public_counts != trace_counts or
            conformance.get('milestone_acceptance_recorded') is not False or
            conformance.get('release_authorized') is not False or
            publication_summary['status'] != 'blocked' or
            publication_summary['release_authorized'] is not False):
        raise ValueError('invalid_m2_milestone_readiness_input')
    bindings = publication_summary['claim_bindings']
    return M2MilestoneReadiness(
        trace.assessed_at,
        M2_TARGET_DATE,
        trace.universe_count,
        trace_counts,
        len(synthetic_stages),
        publication_summary['decision'],
        bindings['required_field_count'],
        bindings['provided_field_count'],
        bindings['missing_field_count'],
    )
