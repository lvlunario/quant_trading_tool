"""Synthetic M2 conformance without promoting public-source readiness."""
from datetime import datetime, timezone

from .m2_acceptance_trace import M2AcceptanceTrace
from .source_workflow import synthetic_source_report


_STAGE_NAMES = (
    'identity', 'source_discovery', 'rights_review',
    'capture_authorization', 'extraction', 'metric_release',
)


def assess_m2_synthetic_conformance(source_bytes, public_trace, *, now=None):
    """Prove the invented path works while the real/public path stays blocked."""
    now = now or datetime.now(timezone.utc)
    if (not isinstance(source_bytes, bytes) or
            not isinstance(public_trace, M2AcceptanceTrace) or
            not isinstance(now, datetime) or now.tzinfo is None):
        raise ValueError('invalid_m2_synthetic_conformance_input')

    synthetic = synthetic_source_report(source_bytes, now=now)
    public = public_trace.public_summary()
    public_counts = [stage['passed_count'] for stage in public['stages']]
    downstream_blocked = (
        public['status'] == 'blocked' and
        public_counts[-2:] == [0, 0] and
        not public['milestone_acceptance_recorded'] and
        not public['release_authorized']
    )
    synthetic_passed = (
        synthetic['status'] == 'ready' and
        synthetic.get('source_sha256') is not None and
        synthetic.get('extraction', {}).get('status') == 'ready' and
        synthetic.get('metric') is not None
    )
    failed_checks = []
    if not synthetic_passed:
        failed_checks.append('synthetic_workflow_blocked')
    if not downstream_blocked:
        failed_checks.append('public_source_boundary_changed')

    return {
        'schema_version': 1,
        'mode': 'synthetic_conformance',
        'status': 'passed' if not failed_checks else 'blocked',
        'assessed_at': now.isoformat(),
        'synthetic_scenario': {
            'status': 'passed' if synthetic_passed else 'blocked',
            'stages': [
                {'gate': name,
                 'status': 'passed' if synthetic_passed else 'not_demonstrated'}
                for name in _STAGE_NAMES
            ],
            'uses_invented_fixture_only': True,
        },
        'public_source_state': {
            'status': public['status'],
            'passed_counts': public_counts,
            'extraction_passed_count': public_counts[-2],
            'metric_release_passed_count': public_counts[-1],
        },
        'failed_checks': failed_checks,
        'milestone_acceptance_recorded': False,
        'release_authorized': False,
        'readiness': ('synthetic technical conformance only; no public source was '
                      'reviewed, captured, extracted or released'),
    }
