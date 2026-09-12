import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def run_json(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'normalized.json'
            path.write_text(json.dumps(payload))
            return subprocess.run([sys.executable, '-m', 'atlas', '--reconcile', str(path)],
                                  capture_output=True, text=True)

    def test_synthetic_demo_is_explicit(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--demo'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['portfolio']['mode'], 'synthetic')
        self.assertEqual(report['hypothetical_put']['expiration_pnl'], '-2801')

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
