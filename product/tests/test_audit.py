from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

from atlas.adapters import NormalizedJsonAdapter
from atlas.audit import ReplayLedger, source_sha256


class AdapterTests(unittest.TestCase):
    def test_normalized_adapter_accepts_object_only(self):
        self.assertEqual(NormalizedJsonAdapter().normalize(b'{"schema_version": 1}'),
                         {'schema_version': 1})
        for source in (b'', b'[]', b'\xff', b'{broken', b' ' * 1_000_001):
            with self.subTest(source=source), self.assertRaises(ValueError):
                NormalizedJsonAdapter().normalize(source)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 12, 23, 55, tzinfo=timezone.utc)
        self.digest = source_sha256(b'synthetic normalized source')

    def test_hash_is_exact_and_deterministic(self):
        self.assertEqual(self.digest, source_sha256(b'synthetic normalized source'))
        self.assertNotEqual(self.digest, source_sha256(b'synthetic normalized source\n'))

    def test_first_attempt_and_exact_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'audit.sqlite3'
            ledger = ReplayLedger(path)
            first = ledger.record(source_id='SRC_12345678', source_hash=self.digest,
                                  outcome='reconciled', observed_at=self.now)
            replay = ledger.record(source_id='SRC_12345678', source_hash=self.digest,
                                   outcome='reconciled', observed_at=self.now)
            self.assertEqual(first.status, 'recorded')
            self.assertEqual(replay.status, 'exact_replay')
            self.assertEqual(replay.first_seen_at, first.first_seen_at)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_reused_id_or_content_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ReplayLedger(Path(directory) / 'audit.sqlite3')
            ledger.record(source_id='SRC_12345678', source_hash=self.digest,
                          outcome='blocked', observed_at=self.now)
            conflicts = (
                ('SRC_12345678', source_sha256(b'different source'), 'blocked'),
                ('SRC_ABCDEFGH', self.digest, 'blocked'),
                ('SRC_12345678', self.digest, 'reconciled'),
            )
            for source_id, digest, outcome in conflicts:
                with self.subTest(source_id=source_id, outcome=outcome), \
                        self.assertRaisesRegex(ValueError, 'source_identity_conflict'):
                    ledger.record(source_id=source_id, source_hash=digest, outcome=outcome,
                                  observed_at=self.now)

    def test_ledger_contains_metadata_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'audit.sqlite3'
            ReplayLedger(path).record(source_id='SRC_12345678', source_hash=self.digest,
                                      outcome='reconciled', observed_at=self.now)
            with sqlite3.connect(path) as connection:
                columns = [row[1] for row in connection.execute('PRAGMA table_info(import_attempts)')]
            self.assertEqual(columns, ['source_id', 'source_sha256', 'outcome', 'first_seen_at'])

    def test_invalid_metadata_is_rejected(self):
        ledger = ReplayLedger(':memory:')
        cases = ({'source_id': 'account-1', 'source_hash': self.digest, 'outcome': 'blocked'},
                 {'source_id': 'SRC_12345678', 'source_hash': 'bad', 'outcome': 'blocked'},
                 {'source_id': 'SRC_12345678', 'source_hash': self.digest, 'outcome': 'unknown'})
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                ledger.record(**case, observed_at=self.now)

    def test_permissive_existing_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'audit.sqlite3'
            path.touch(mode=0o644)
            with self.assertRaisesRegex(ValueError, 'insecure_ledger_permissions'):
                ReplayLedger(path).record(source_id='SRC_12345678', source_hash=self.digest,
                                          outcome='reconciled', observed_at=self.now)
