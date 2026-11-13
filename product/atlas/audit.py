"""Hash-only audit ledger for exact-source replay protection.

The ledger stores no portfolio rows, symbols, quantities, prices, or account
totals. A digest is an integrity identifier, not anonymization.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
from typing import Literal


@dataclass(frozen=True)
class LedgerResult:
    status: Literal['recorded', 'exact_replay']
    first_seen_at: str


def source_sha256(source: bytes) -> str:
    """Return a digest of the exact bytes supplied to an adapter."""
    if not isinstance(source, bytes) or not source:
        raise ValueError('invalid_source_bytes')
    return hashlib.sha256(source).hexdigest()


class ReplayLedger:
    """Atomically register import attempts in a local SQLite ledger."""

    def __init__(self, path: str | Path):
        if not isinstance(path, (str, Path)) or not str(path):
            raise ValueError('invalid_ledger_path')
        self.path = str(path)

    def record(self, *, source_id: str, source_hash: str,
               outcome: Literal['reconciled', 'blocked'], observed_at=None) -> LedgerResult:
        if not isinstance(source_id, str) or not re.fullmatch(r'SRC_[A-Z0-9]{8,32}', source_id):
            raise ValueError('invalid_source_id')
        if not isinstance(source_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', source_hash):
            raise ValueError('invalid_source_hash')
        if outcome not in ('reconciled', 'blocked'):
            raise ValueError('invalid_import_outcome')
        observed_at = observed_at or datetime.now(timezone.utc)
        if not isinstance(observed_at, datetime) or observed_at.tzinfo is None:
            raise ValueError('invalid_observed_at')
        timestamp = observed_at.astimezone(timezone.utc).isoformat()

        existed = self.path != ':memory:' and Path(self.path).exists()
        if self.path != ':memory:':
            path = Path(self.path)
            if path.is_symlink():
                raise ValueError('invalid_ledger_path')
            if existed and stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise ValueError('insecure_ledger_permissions')
            if not existed:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
        try:
            with sqlite3.connect(self.path, isolation_level=None, timeout=5) as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS import_attempts (
                       source_id TEXT PRIMARY KEY,
                       source_sha256 TEXT NOT NULL UNIQUE,
                       outcome TEXT NOT NULL CHECK(outcome IN ('reconciled', 'blocked')),
                       first_seen_at TEXT NOT NULL)""")
                connection.execute('BEGIN IMMEDIATE')
                by_id = connection.execute(
                    'SELECT source_sha256, outcome, first_seen_at FROM import_attempts WHERE source_id = ?',
                    (source_id,)).fetchone()
                by_hash = connection.execute(
                    'SELECT source_id, outcome, first_seen_at FROM import_attempts WHERE source_sha256 = ?',
                    (source_hash,)).fetchone()
                if by_id or by_hash:
                    if (by_id and by_hash and by_id[0] == source_hash and
                            by_id[1] == outcome and by_hash[0] == source_id):
                        connection.execute('COMMIT')
                        return LedgerResult('exact_replay', by_id[2])
                    connection.execute('ROLLBACK')
                    raise ValueError('source_identity_conflict')
                connection.execute(
                    'INSERT INTO import_attempts VALUES (?, ?, ?, ?)',
                    (source_id, source_hash, outcome, timestamp))
                connection.execute('COMMIT')
        except sqlite3.Error:
            raise ValueError('ledger_unavailable') from None
        return LedgerResult('recorded', timestamp)
