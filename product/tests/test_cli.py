import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def run_json(self, payload, ledger=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'normalized.json'
            path.write_text(json.dumps(payload))
            command = [sys.executable, '-m', 'atlas', '--reconcile', str(path)]
            if ledger:
                command.extend(['--ledger', str(ledger)])
            return subprocess.run(command,
                                  capture_output=True, text=True)

    def test_synthetic_demo_is_explicit(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--demo'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['portfolio']['mode'], 'synthetic')
        self.assertEqual(report['hypothetical_put']['expiration_pnl'], '-2801')

    def test_research_demo_runs_combined_synthetic_gate(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--research-demo'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual((report['mode'], report['status']), ('synthetic', 'ready'))
        self.assertIn('no real data', report['readiness'])

    def test_broker_demo_runs_lossless_mapping_without_position_echo(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--broker-demo'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual((report['mode'], report['status']), ('synthetic', 'reconciled'))
        self.assertEqual(report['mapping_contract'], 'synthetic_broker_v1')
        self.assertEqual(report['input_row_count'], report['mapped_row_count'])
        self.assertIn('not Fidelity-validated', report['readiness'])
        self.assertIn('invented values only', report['data_notice'])
        for private_field in ('"symbol"', '"ticker"', '"quantity"', '"price"'):
            self.assertNotIn(private_field, run.stdout)

    def test_synthetic_csv_demo_hashes_exact_fixture_and_redacts_positions(self):
        fixture = Path(__file__).parents[1] / 'fixtures' / 'synthetic-broker.csv'
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--synthetic-csv-demo', str(fixture)],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual((report['mode'], report['status']), ('synthetic', 'reconciled'))
        self.assertEqual(report['parser_contract'], 'synthetic_delimited_v1')
        self.assertEqual(report['source_sha256'], hashlib.sha256(fixture.read_bytes()).hexdigest())
        self.assertIn('runtime timestamp', report['data_notice'])
        for private_field in ('"symbol"', '"ticker"', '"quantity"', '"price"'):
            self.assertNotIn(private_field, run.stdout)

    def test_synthetic_csv_demo_blocks_invalid_rows_without_echoing_them(self):
        source = ('account_key,row_type,ticker,quantity,price,market_value\n'
                  'ALPHA,CASH,,0,0,75\n'
                  'PRIVATE-MARKER,EXTRA\n'
                  'ALPHA,ACCOUNT_TOTAL,,,,75\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private-export.csv'
            path.write_text(source)
            run = subprocess.run(
                [sys.executable, '-m', 'atlas', '--synthetic-csv-demo', str(path)],
                capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual(report['status'], 'blocked')
        self.assertNotIn('PRIVATE-MARKER', run.stdout + run.stderr)
        self.assertNotIn('private-export', run.stdout + run.stderr)

    def test_invalid_input_rejected_without_content_or_path_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private-account.json'
            path.write_text('{private-sensitive-test-value')
            run = subprocess.run([sys.executable, '-m', 'atlas', '--snapshot', str(path)],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, '')
        self.assertNotIn('private-sensitive-test-value', run.stderr)
        self.assertNotIn('private-account', run.stderr)

    def test_reconciliation_cli_succeeds_without_echoing_positions(self):
        from datetime import datetime, timezone
        payload = {'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
                   'source_type': 'normalized_synthetic', 'source_id': 'SRC_12345678',
                   'as_of': datetime.now(timezone.utc).isoformat(),
                   'expected_totals': {'ACCT_ALPHA': '100'},
                   'rows': [{'account_alias': 'ACCT_ALPHA', 'asset_type': 'equity',
                             'symbol': 'DEMO', 'quantity': '2.5', 'price': '10',
                             'market_value': '25'},
                            {'account_alias': 'ACCT_ALPHA', 'asset_type': 'cash',
                             'symbol': '', 'quantity': '0', 'price': '0',
                             'market_value': '75'}]}
        run = self.run_json(payload)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['status'], 'reconciled')
        self.assertEqual(report['replay_status'], 'not_checked')
        self.assertEqual(len(report['source_sha256']), 64)
        self.assertNotIn('DEMO', run.stdout)

    def test_blocked_reconciliation_has_distinct_exit_code(self):
        from datetime import datetime, timezone
        payload = {'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
                   'source_type': 'normalized_synthetic', 'source_id': 'SRC_12345678',
                   'as_of': datetime.now(timezone.utc).isoformat(),
                   'expected_totals': {'ACCT_ALPHA': '101'},
                   'rows': [{'account_alias': 'ACCT_ALPHA', 'asset_type': 'cash',
                             'symbol': '', 'quantity': '0', 'price': '0',
                             'market_value': '100'}]}
        run = self.run_json(payload)
        self.assertEqual(run.returncode, 3)
        self.assertEqual(json.loads(run.stdout)['status'], 'blocked')

    def test_ledger_suppresses_exact_replay_publication(self):
        from datetime import datetime, timezone
        payload = {'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
                   'source_type': 'normalized_synthetic', 'source_id': 'SRC_12345678',
                   'as_of': datetime.now(timezone.utc).isoformat(),
                   'expected_totals': {'ACCT_ALPHA': '100'},
                   'rows': [{'account_alias': 'ACCT_ALPHA', 'asset_type': 'cash',
                             'symbol': '', 'quantity': '0', 'price': '0',
                             'market_value': '100'}]}
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'audit.sqlite3'
            first = self.run_json(payload, ledger)
            replay = self.run_json(payload, ledger)
        self.assertEqual(json.loads(first.stdout)['replay_status'], 'recorded')
        report = json.loads(replay.stdout)
        self.assertEqual(report['replay_status'], 'exact_replay')
        self.assertEqual(report['publishable_row_count'], 0)
        self.assertEqual(replay.returncode, 0)

    def test_ledger_cannot_be_used_with_other_commands(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--demo', '--ledger', 'audit.db'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)

    def test_preview_port_requires_preview_server(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--demo',
                              '--preview-port', '8765'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn('8765', run.stderr)
