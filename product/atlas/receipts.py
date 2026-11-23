"""Minimal presentation receipt for completed reconciliation attempts."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ImportReceipt:
    schema_version: int
    mode: str
    reconciliation: str
    replay: str
    input_rows: int
    rejected_rows: int
    publishable_rows: int
    decision: str

    def to_dict(self):
        return asdict(self)


def import_receipt(report: dict) -> ImportReceipt:
    """Project a trusted engine report; reject inconsistent publication states.

    No account aliases, totals, paths, free text or position fields are copied.
    This is a presentation contract, not independent financial validation.
    """
    mode = report.get('mode')
    status = report.get('status')
    replay = report.get('replay_status')
    rows = report.get('outcomes')
    count = report.get('publishable_row_count')
    errors = report.get('errors')
    if (mode not in ('synthetic', 'user_export') or
            status not in ('reconciled', 'blocked') or
            replay not in ('not_checked', 'recorded', 'exact_replay') or
            not isinstance(rows, list) or not 1 <= len(rows) <= 10000 or
            not isinstance(errors, list) or type(count) is not int or count < 0):
        raise ValueError('invalid_receipt_report')
    rejected = 0
    for index, row in enumerate(rows, 1):
        if (not isinstance(row, dict) or type(row.get('row_number')) is not int or
                row['row_number'] != index or
                row.get('status') not in ('accepted', 'rejected')):
            raise ValueError('invalid_receipt_rows')
        rejected += row['status'] == 'rejected'
    if status == 'reconciled' and (rejected or errors):
        raise ValueError('inconsistent_receipt_status')
    expected = len(rows) if status == 'reconciled' and replay != 'exact_replay' else 0
    if count != expected or (status == 'blocked' and not errors):
        raise ValueError('inconsistent_receipt_publication')
    decision = ('blocked' if status == 'blocked' else
                'duplicate' if replay == 'exact_replay' else
                'replay_check_required' if replay == 'not_checked' else 'eligible')
    return ImportReceipt(1, mode, status, replay, len(rows), rejected, count, decision)
