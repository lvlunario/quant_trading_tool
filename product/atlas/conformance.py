"""Public-safe M1 conformance statement for the synthetic import boundary."""
from dataclasses import asdict, dataclass


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
              for status in ('verified_synthetic', 'blocked_external_evidence',
                             'not_implemented')}
    return {
        'schema_version': 1,
        'phase': 'M1 Portfolio Truth',
        'milestone_date': '2026-10-03',
        'overall_status': 'partial_synthetic_only',
        'counts': counts,
        'checks': serialized,
    }
