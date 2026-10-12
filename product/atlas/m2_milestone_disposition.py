"""Fail-closed M2 checkpoint disposition; never records acceptance."""
from dataclasses import dataclass
from datetime import date, datetime

from .m2_milestone_readiness import M2MilestoneReadiness, M2_TARGET_DATE


CRITERION_ORDER = (
    'identity',
    'source_discovery',
    'rights_review',
    'capture_authorization',
    'extraction',
    'metric_release',
)
CRITERION_CONTRACT = {
    'identity': (9, 'identity_unresolved'),
    'source_discovery': (9, 'source_candidate_missing'),
    'rights_review': (8, 'rights_review_incomplete'),
    'capture_authorization': (8, 'capture_authorization_incomplete'),
    'extraction': (9, 'no_authorized_source_bytes'),
    'metric_release': (9, 'no_verified_metric_evidence'),
}


@dataclass(frozen=True)
class M2CriterionDisposition:
    criterion: str
    passed_count: int
    required_count: int
    blocker: str
    recommendation: str

    def __post_init__(self):
        expected_required, expected_blocker = CRITERION_CONTRACT.get(
            self.criterion, (None, None))
        if (self.criterion not in CRITERION_ORDER or
                not isinstance(self.passed_count, int) or
                isinstance(self.passed_count, bool) or
                not isinstance(self.required_count, int) or
                isinstance(self.required_count, bool) or
                not 0 <= self.passed_count <= self.required_count or
                not isinstance(self.blocker, str) or not self.blocker or
                self.required_count != expected_required or
                self.recommendation not in
                ('recommend_review', 'recommend_defer') or
                (self.recommendation == 'recommend_review') !=
                (self.passed_count == self.required_count) or
                (self.blocker != ('none' if self.recommendation ==
                                  'recommend_review' else expected_blocker))):
            raise ValueError('invalid_m2_criterion_disposition')


@dataclass(frozen=True)
class M2MilestoneDisposition:
    assessed_at: datetime
    checkpoint_date: date
    criteria: tuple[M2CriterionDisposition, ...]
    publication_decision: str
    synthetic_controls_status: str

    def __post_init__(self):
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.checkpoint_date != M2_TARGET_DATE or
                tuple(item.criterion for item in self.criteria) !=
                CRITERION_ORDER or
                self.publication_decision != 'withhold_publication' or
                self.synthetic_controls_status != 'ready_for_review'):
            raise ValueError('invalid_m2_milestone_disposition')

    def public_summary(self):
        deferred = sum(item.recommendation == 'recommend_defer'
                       for item in self.criteria)
        days_to_checkpoint = (self.checkpoint_date -
                              self.assessed_at.date()).days
        if days_to_checkpoint > 0:
            checkpoint_status = 'scheduled'
        elif days_to_checkpoint == 0:
            checkpoint_status = 'due'
        else:
            checkpoint_status = 'elapsed'
        return {
            'schema_version': 1,
            'receipt_state': 'candidate',
            'status': 'blocked' if deferred else 'ready_for_founder_review',
            'phase': 'M2 Sourced Research',
            'assessed_at': self.assessed_at.isoformat(),
            'checkpoint_date': self.checkpoint_date.isoformat(),
            'checkpoint_status': checkpoint_status,
            'criteria': [
                {
                    'criterion': item.criterion,
                    'recommendation': item.recommendation,
                    'passed_count': item.passed_count,
                    'required_count': item.required_count,
                    'blocker': item.blocker,
                }
                for item in self.criteria
            ],
            'review_recommended_count': len(self.criteria) - deferred,
            'deferred_count': deferred,
            'overall_recommendation': (
                'defer_unresolved_criteria' if deferred else
                'submit_for_founder_review'),
            'synthetic_controls_status': self.synthetic_controls_status,
            'weekly_publication_decision': self.publication_decision,
            'founder_response_recorded': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
        }


def recommend_m2_milestone_disposition(readiness):
    """Map every sourced criterion to review or explicit deferral."""
    if not isinstance(readiness, M2MilestoneReadiness):
        raise ValueError('invalid_m2_milestone_disposition_input')
    summary = readiness.public_summary()
    criteria = summary.get('sourced_exit_criteria')
    if (summary.get('status') != 'blocked' or
            summary.get('target_date') != M2_TARGET_DATE.isoformat() or
            summary.get('milestone_acceptance_recorded') is not False or
            summary.get('release_authorized') is not False or
            summary.get('weekly_publication', {}).get('decision') !=
            'withhold_publication' or
            not isinstance(criteria, list) or len(criteria) != 6 or
            tuple(item.get('criterion') for item in criteria) !=
            CRITERION_ORDER):
        raise ValueError('invalid_m2_milestone_disposition_input')
    dispositions = tuple(
        M2CriterionDisposition(
            item['criterion'],
            item['passed_count'],
            item['required_count'],
            ('none' if item['status'] == 'ready' else item['blocker']),
            ('recommend_review' if item['status'] == 'ready' else
             'recommend_defer'),
        )
        for item in criteria
    )
    return M2MilestoneDisposition(
        readiness.assessed_at,
        M2_TARGET_DATE,
        dispositions,
        summary['weekly_publication']['decision'],
        summary['synthetic_controls']['status'],
    )
