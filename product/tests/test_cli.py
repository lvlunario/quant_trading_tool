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

    def test_source_demo_runs_fixed_fixture_without_raw_content(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--source-demo'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual((report['mode'], report['status']), ('synthetic', 'ready'))
        self.assertEqual(report['metric']['value'], '123.40')
        self.assertNotIn('source_uri', run.stdout)
        self.assertNotIn('Reported revenue', run.stdout)

    def test_extractor_conformance_demo_is_synthetic_and_redacted(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--extractor-conformance-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['status'], 'conformant_synthetic')
        self.assertEqual(report['matched_case_count'], 6)
        self.assertIn('no real provider', report['qualification'])
        self.assertNotIn('Reported revenue', run.stdout)
        self.assertNotIn('"source"', run.stdout)

    def test_provider_qualification_demo_blocks_without_external_evidence(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--provider-qualification-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['evidence_scope'], 'none')
        self.assertFalse(report['release_authorized'])
        self.assertIn('authorization_evidence_missing', report['codes'])
        for private_field in ('corpus_digest', 'reviewer_ids', 'receipt_id'):
            self.assertNotIn(private_field, run.stdout)

    def test_m1_handoff_advances_without_recording_approval(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--m1-handoff'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['next_phase'], 'M2 Sourced Research')
        self.assertEqual(report['fidelity_state'],
                         'deferred_pending_private_evidence')
        self.assertFalse(report['founder_approval_recorded'])
        self.assertFalse(report['release_authorized'])
        for private_field in ('account_id', 'position', 'source_sha256'):
            self.assertNotIn(private_field, run.stdout)

    def test_watchlist_registry_demo_reports_identity_not_market_data(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--watchlist-registry-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual((report['resolved_count'], report['blocked_count']), (8, 1))
        self.assertEqual(report['blocked'][0]['symbol'], 'CRBS')
        self.assertIn('AVGO', report['resolved_symbols'])
        for excluded in ('"price"', '"quantity"', '"account"', '"recommendation"'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_source_catalog_demo_withholds_metrics_and_recommendations(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--source-catalog-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['candidate_count'], 8)
        self.assertTrue(all(item['metric_status'] == 'unavailable'
                            for item in report['items']))
        self.assertTrue(all(item['decision'] ==
                            'blocked_pending_rights_and_extraction'
                            for item in report['items']))
        for excluded in ('"metric_value"', '"price"', '"recommendation"'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_source_rights_demo_blocks_retrieval_without_evidence(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--source-rights-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual((report['status'], report['review_count']), ('blocked', 8))
        self.assertFalse(report['retrieval_policy']['network_fetch_enabled'])
        self.assertTrue(all(item['decision'] == 'terms_evidence_required'
                            for item in report['items']))
        for excluded in ('"source_uri"', '"terms_uri"', '"evidence_sha256"',
                         '"metric_value"', '"recommendation"'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_rights_evidence_demo_reports_missing_reviews_safely(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--rights-evidence-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual((report['status'], report['rights_allowed_count']),
                         ('blocked', 0))
        self.assertTrue(all(item['decision'] == 'missing_review_evidence'
                            for item in report['items']))
        self.assertFalse(report['release_authorized'])
        for excluded in ('"terms_uri"', '"evidence_sha256"', '"review_id"',
                         '"reviewer_reference"', '"metric_value"'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_rights_review_worksheet_demo_is_blank_and_blocked(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--rights-review-worksheet-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual((report['status'], report['candidate_count']),
                         ('blocked', 8))
        self.assertTrue(report['template_only'])
        self.assertTrue(all(item['review_state'] == 'not_started'
                            for item in report['items']))
        self.assertTrue(all(step['status'] == 'pending'
                            for step in report['checklist']))
        self.assertFalse(report['release_authorized'])
        for excluded in ('"reviewer_reference":', '"terms_uri":',
                         '"evidence_sha256":', '"conclusion":'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_source_capture_authorization_demo_requires_both_keys(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas',
             '--source-capture-authorization-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual((report['candidate_count'],
                          report['rights_ready_count'],
                          report['capture_authorized_count']), (8, 0, 0))
        self.assertEqual(report['source_bytes_status'], 'not_provided')
        self.assertFalse(report['release_authorized'])
        for excluded in ('authorization_id', 'document_id', 'source_uri',
                         'terms_uri', 'evidence_sha256', 'reviewer_reference'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_research_work_items_demo_reports_gaps_without_evidence(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--research-work-items-demo'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual((report['work_item_count'], report['blocked_count']),
                         (9, 9))
        self.assertEqual((report['catalogued_source_count'],
                          report['rights_allowed_count']), (8, 0))
        self.assertFalse(report['release_authorized'])
        for excluded in ('source_uri', 'terms_uri', 'document_id', 'review_id',
                         'sha256', 'metric_value', '"recommendation"'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_m2_acceptance_trace_is_ordered_public_and_blocked(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--m2-acceptance-trace'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        report = json.loads(run.stdout)
        self.assertEqual([item['passed_count'] for item in report['stages']],
                         [8, 8, 0, 0, 0, 0])
        self.assertFalse(report['milestone_acceptance_recorded'])
        self.assertFalse(report['release_authorized'])
        for excluded in ('symbol', 'source_uri', 'terms_uri', 'document_id',
                         'authorization_id', 'review_id', 'sha256',
                         'metric_value', 'recommendation'):
            self.assertNotIn(excluded, run.stdout.lower())

    def test_m2_synthetic_conformance_keeps_public_release_blocked(self):
        run = subprocess.run(
            [sys.executable, '-m', 'atlas', '--m2-synthetic-conformance'],
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['public_source_state']['passed_counts'],
                         [8, 8, 0, 0, 0, 0])
        self.assertTrue(all(
            item['status'] == 'passed'
            for item in report['synthetic_scenario']['stages']))
        self.assertFalse(report['release_authorized'])
        for excluded in ('document_id', 'observation_id', 'source_sha256',
                         'source_uri', 'terms_uri', 'metric_id', '123.40',
                         'symbol', 'recommendation'):
            self.assertNotIn(excluded, run.stdout.lower())

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
        self.assertEqual(report['replay_status'], 'not_checked')
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

    def test_synthetic_csv_ledger_suppresses_exact_replay(self):
        fixture = Path(__file__).parents[1] / 'fixtures' / 'synthetic-broker.csv'
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'synthetic-receipts.sqlite3'
            command = [sys.executable, '-m', 'atlas', '--synthetic-csv-demo',
                       str(fixture), '--ledger', str(ledger)]
            first = subprocess.run(command, capture_output=True, text=True)
            replay = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(json.loads(first.stdout)['replay_status'], 'recorded')
        self.assertEqual(replay.returncode, 0)
        report = json.loads(replay.stdout)
        self.assertEqual(report['replay_status'], 'exact_replay')
        self.assertEqual(report['publishable_row_count'], 0)
        self.assertIn('do not publish', report['readiness'])

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
