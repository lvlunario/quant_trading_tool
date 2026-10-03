"""Public-safe M1 conformance statement for the synthetic import boundary."""
from dataclasses import asdict, dataclass


_STATUSES = ('verified_synthetic', 'blocked_external_evidence', 'not_implemented')


@dataclass(frozen=True)
class ConformanceCheck:
    check_id: str
    capability: str
    status: str
    evidence: str
    limitation: str

    def to_dict(self):
        return asdict(self)


def m1_import_conformance() -> dict:
    """Return a fixed evidence map without customer data or compatibility claims."""
    checks = (
        ConformanceCheck(
            'SYN_ROW_ACCOUNTING', 'Every source record receives an outcome',
            'verified_synthetic', 'Synthetic malformed and unsupported-row tests',
            'Real Fidelity row types have not been observed.'),
        ConformanceCheck(
            'SYN_RECONCILIATION', 'Positions and account totals reconcile exactly',
            'verified_synthetic', 'Synthetic cash, equity and total-mismatch tests',
            'Source-specific rounding has not been established.'),
        ConformanceCheck(
            'SYN_REPLAY', 'Exact retries cannot republish through the private ledger',
            'verified_synthetic', 'SQLite first-attempt and exact-replay tests',
            'The browser demo intentionally uses no persistence.'),
        ConformanceCheck(
            'SYN_RECEIPT', 'UI receipt excludes financial and account fields',
            'verified_synthetic', 'Receipt allowlist and HTTP privacy tests',
            'This is presentation minimization, not anonymization.'),
        ConformanceCheck(
            'FID_FORMAT', 'Fidelity headers, footers and row classifications',
            'blocked_external_evidence', 'Representative export not reviewed',
            'No Fidelity-specific parser or compatibility claim.'),
        ConformanceCheck(
            'FID_CASH', 'Fidelity cash and core-position semantics',
            'blocked_external_evidence', 'Representative export not reviewed',
            'Atlas will not infer whether a fund row represents cash.'),
        ConformanceCheck(
            'FID_OPTIONS', 'Fidelity option symbology and unsettled activity',
            'blocked_external_evidence', 'Representative export not reviewed',
            'Options and unknown activity remain blocking rows.'),
        ConformanceCheck(
            'FID_ROUNDING', 'Fidelity valuation and rounding rules',
            'blocked_external_evidence', 'Representative export not reviewed',
            'Synthetic mapping requires exact arithmetic.'),
        ConformanceCheck(
            'PRIVATE_STORAGE', 'Authorized private import persistence',
            'not_implemented', 'Private destination selected but not provisioned',
            'Public repository remains synthetic-only.'),
    )
    serialized = [check.to_dict() for check in checks]
    counts = {status: sum(check.status == status for check in checks)
              for status in _STATUSES}
    return {
        'schema_version': 1,
        'phase': 'M1 Portfolio Truth',
        'milestone_date': '2026-10-03',
        'overall_status': 'partial_synthetic_only',
        'counts': counts,
        'checks': serialized,
    }


def recommend_m1_disposition(report=None) -> dict:
    """Derive a bounded milestone recommendation; never record acceptance."""
    report = report or m1_import_conformance()
    if (not isinstance(report, dict) or report.get('schema_version') != 1 or
            report.get('phase') != 'M1 Portfolio Truth' or
            report.get('milestone_date') != '2026-10-03' or
            report.get('overall_status') != 'partial_synthetic_only' or
            not isinstance(report.get('checks'), list) or
            not isinstance(report.get('counts'), dict)):
        raise ValueError('invalid_m1_conformance')
    checks = report['checks']
    ids = [check.get('check_id') for check in checks if isinstance(check, dict)]
    actual = {status: sum(check.get('status') == status for check in checks
                          if isinstance(check, dict)) for status in _STATUSES}
    if (len(ids) != len(checks) or len(ids) != len(set(ids)) or
            set(report['counts']) != set(_STATUSES) or
            report['counts'] != actual or any(
                check.get('status') not in _STATUSES for check in checks
                if isinstance(check, dict))):
        raise ValueError('inconsistent_m1_conformance')
    fidelity = [check for check in checks
                if check['check_id'].startswith('FID_')]
    if (actual['verified_synthetic'] < 1 or not fidelity or
            any(check['status'] != 'blocked_external_evidence'
                for check in fidelity)):
        raise ValueError('unsupported_m1_disposition')
    return {
        'schema_version': 1,
        'evaluated_milestone': report['milestone_date'],
        'synthetic_scope': 'recommend_accept_engineering_evidence',
        'fidelity_scope': 'recommend_defer_external_validation',
        'phase_progression': 'continue_synthetic_fallback',
        'december_target': 'unchanged_conditional',
        'founder_approval_recorded': False,
        'release_authorized': False,
        'required_before_fidelity_acceptance': (
            'provisioned_private_boundary',
            'authorized_representative_export',
            'source_specific_profile_and_reconciliation_evidence',
        ),
    }


def m1_milestone_handoff(report=None) -> dict:
    """Finalize the delegated engineering handoff without granting acceptance.

    The handoff is intentionally derived from the validated disposition rather
    than maintained as a second independent set of milestone claims.
    """
    disposition = recommend_m1_disposition(report)
    if (disposition['synthetic_scope'] !=
            'recommend_accept_engineering_evidence' or
            disposition['fidelity_scope'] !=
            'recommend_defer_external_validation' or
            disposition['phase_progression'] !=
            'continue_synthetic_fallback' or
            disposition['founder_approval_recorded'] is not False or
            disposition['release_authorized'] is not False):
        raise ValueError('unsupported_m1_handoff')
    return {
        'schema_version': 1,
        'milestone': 'M1 Portfolio Truth',
        'milestone_date': disposition['evaluated_milestone'],
        'engineering_state': 'synthetic_scope_accepted_for_progression',
        'fidelity_state': 'deferred_pending_private_evidence',
        'next_phase': 'M2 Sourced Research',
        'next_deadline': '2026-10-17',
        'december_target': disposition['december_target'],
        'founder_approval_recorded': False,
        'release_authorized': False,
        'data_notice': ('public-safe engineering handoff; no holdings, account '
                        'data, Fidelity export or private evidence'),
    }
