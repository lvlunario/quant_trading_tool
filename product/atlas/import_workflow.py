"""Shared synthetic import workflow for CLI and local preview adapters."""
from datetime import datetime, timezone
from pathlib import Path

from .audit import ReplayLedger, source_sha256
from .broker_mapping import parse_synthetic_delimited
from .receipts import import_receipt


def apply_replay_gate(report: dict, source_hash: str,
                      ledger_path: Path | None) -> None:
    """Attach replay evidence and suppress publication on an exact retry."""
    report['source_sha256'] = source_hash
    report['replay_status'] = 'not_checked'
    if ledger_path:
        ledger_result = ReplayLedger(ledger_path).record(
            source_id=report['source_id'], source_hash=source_hash,
            outcome=report['status'])
        report['replay_status'] = ledger_result.status
        report['first_seen_at'] = ledger_result.first_seen_at
        if ledger_result.status == 'exact_replay':
            report['publishable_row_count'] = 0
            report['readiness'] = 'exact replay; do not publish positions again'
    report['receipt'] = import_receipt(report).to_dict()


def synthetic_csv_report(source_bytes: bytes, *, now=None,
                         ledger_path: Path | None = None) -> dict:
    """Run the fixed synthetic CSV contract without accepting a source path."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('aware_now_required')
    digest = source_sha256(source_bytes)
    report = parse_synthetic_delimited(
        source_bytes, source_id=f'SRC_{digest[:16].upper()}',
        as_of=now.isoformat(), now=now)
    apply_replay_gate(report, digest, ledger_path)
    report['data_notice'] = (
        'invented synthetic fixture only; runtime timestamp; '
        'no broker file or account access')
    return report
