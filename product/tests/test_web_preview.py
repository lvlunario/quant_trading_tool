from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread
from urllib.parse import urlencode
import unittest

from atlas.web_preview import (calculate_put, make_handler, render_import_demo,
                               render_m1_status, render_page, serve_preview)


class WebPreviewTests(unittest.TestCase):
    def setUp(self):
        self.token = "TEST_TOKEN"
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(self.token))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    @property
    def values(self):
        return {"strike": ["50"], "premium_per_share": ["2"],
                "terminal_price": ["0"], "fees": ["0"],
                "available_cash": ["5000"]}

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read().decode()
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, response_headers, data

    def test_kernel_calculation_and_strict_fields(self):
        _, result = calculate_put(self.values)
        self.assertEqual(result["expiration_pnl"], "-4800")
        for invalid in ({}, dict(self.values, strike=["50", "51"]),
                        dict(self.values, unexpected=["1"])):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                calculate_put(invalid)

    def test_html_escapes_token_and_has_no_script_or_external_asset(self):
        page = render_page(token='"><script>bad</script>')
        self.assertNotIn('<script>bad</script>', page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("https://", page)
        self.assertIn("Synthetic inputs only", page)

    def test_get_has_security_headers_and_no_store(self):
        status, headers, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("form-action 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn('name="token" value="TEST_TOKEN"', page)

    def test_valid_post_returns_kernel_result(self):
        fields = {key: value[0] for key, value in self.values.items()}
        fields["token"] = self.token
        body = urlencode(fields)
        status, _, page = self.request(
            "POST", "/calculate", body,
            {"Content-Type": "application/x-www-form-urlencoded",
             "Content-Length": str(len(body))})
        self.assertEqual(status, 200)
        self.assertIn("-$4800", page)
        self.assertIn("Gross cash required", page)

    def test_invalid_token_and_bad_cash_fail_closed(self):
        fields = {key: value[0] for key, value in self.values.items()}
        for token, cash, expected_status in (("wrong", "5000", 403),
                                              (self.token, "4999", 400)):
            fields.update(token=token, available_cash=cash)
            body = urlencode(fields)
            status, _, page = self.request(
                "POST", "/calculate", body,
                {"Content-Type": "application/x-www-form-urlencoded",
                 "Content-Length": str(len(body))})
            self.assertEqual(status, expected_status)
            self.assertIn("Scenario blocked", page)

    def test_wrong_host_path_and_oversize_request_are_rejected(self):
        status, _, _ = self.request("GET", "/missing")
        self.assertEqual(status, 404)
        status, _, _ = self.request("POST", "/calculate", "x",
                                    {"Content-Type": "application/x-www-form-urlencoded",
                                     "Content-Length": "2049"})
        self.assertEqual(status, 413)

    def test_server_rejects_privileged_or_invalid_port(self):
        for port in (0, 80, 65536, "8765", True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                serve_preview(port)

    def test_overview_links_to_interactive_lab_and_readonly_checklist(self):
        status, headers, page = self.request("GET", "/overview")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn('href="/">Open interactive Options Lab', page)
        self.assertIn('href="/import-demo">Run fixed synthetic import demo', page)
        self.assertIn('href="/m1-status">View M1 conformance', page)
        self.assertIn('href="/checklist"', page)
        self.assertNotIn('<!-- interactive-options-link -->', page)
        for section in ('overview', 'portfolio', 'research', 'options', 'weekly'):
            self.assertIn(f'id="{section}"', page)
        _, _, lab = self.request("GET", "/")
        self.assertIn('href="/overview"', lab)

    def test_provider_qualification_projection_is_blocked_and_redacted(self):
        status, _, page = self.request("GET", "/overview")
        self.assertEqual(status, 200)
        self.assertIn('data-qualification="status" data-value="blocked"', page)
        self.assertIn('data-qualification="release_authorized" data-value="false"',
                      page)
        self.assertIn('private_boundary_evidence_missing', page)
        for private_field in ('corpus_digest', 'label_set_digest', 'reviewer_ids',
                              'authorization_receipt_id'):
            self.assertNotIn(private_field, page)

    def test_rights_projection_is_blocked_and_redacted(self):
        status, _, page = self.request("GET", "/overview")
        self.assertEqual(status, 200)
        self.assertIn('data-rights="status" data-value="blocked"', page)
        self.assertEqual(page.count('data-value="missing_review_evidence"'), 3)
        self.assertIn(
            'data-rights="technical_retrieval_status" '
            'data-value="disabled_separate_gate"', page)
        self.assertIn('data-rights="release_authorized" data-value="false"', page)
        for private_field in ('terms_uri', 'evidence_sha256', 'reviewer_reference',
                              'review_id'):
            self.assertNotIn(private_field, page)

    def test_import_demo_runs_fixed_fixture_through_redacted_contract(self):
        status, headers, page = self.request("GET", "/import-demo")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn('data-import-decision="replay_check_required"', page)
        self.assertIn('data-reconciliation="reconciled"', page)
        self.assertIn('data-replay="not_checked"', page)
        self.assertIn('data-input-rows="2"', page)
        self.assertIn('data-rejected-rows="0"', page)
        self.assertIn('data-publishable-rows="2"', page)
        self.assertIn('synthetic_delimited_v1', page)

    def test_import_demo_has_no_input_or_position_disclosure(self):
        page = render_import_demo()
        self.assertNotIn('<form', page)
        self.assertNotIn('<input', page)
        for private_marker in ('DEMO', 'ALPHA', '$25', '$75', 'source_sha256'):
            self.assertNotIn(private_marker, page)
        self.assertIn('No upload', page)

    def test_m1_status_separates_synthetic_evidence_from_blockers(self):
        status, headers, page = self.request("GET", "/m1-status")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(page.count('data-status="verified_synthetic"'), 4)
        self.assertEqual(page.count('data-status="blocked_external_evidence"'), 4)
        self.assertEqual(page.count('data-status="not_implemented"'), 1)
        self.assertIn('not founder approval', page)
        self.assertIn('not founder approval', render_m1_status())
        self.assertIn('data-synthetic-disposition="recommend_accept_engineering_evidence"', page)
        self.assertIn('data-fidelity-disposition="recommend_defer_external_validation"', page)
        self.assertIn('data-phase-progression="continue_synthetic_fallback"', page)
        self.assertIn('No founder approval or release authorization is recorded', page)
        self.assertNotIn('<form', page)

    def test_checklist_is_readonly_and_arbitrary_files_are_not_served(self):
        status, _, page = self.request("GET", "/checklist")
        self.assertEqual(status, 200)
        self.assertIn('no decisions are saved or approved', page)
        self.assertIn('M6', page)
        self.assertNotIn('<form', page)
        for path in ('/.env', '/../.env', '/docs/PROGRAM.md', '/overview?file=.env'):
            status, _, _ = self.request("GET", path)
            self.assertEqual(status, 404)
