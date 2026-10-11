from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread
from urllib.parse import urlencode
import unittest

from atlas.web_preview import (calculate_put, make_handler, render_import_demo,
                               render_m1_status, render_page,
                               public_m2_acceptance_trace,
                               public_m2_synthetic_conformance,
                               render_research_work_items, render_weekly_review,
                               serve_preview)


RESEARCH_PATHS = (
    "/research-work-items", "/research-work-items/identity",
    "/research-work-items/source", "/research-work-items/rights",
)


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
        self.assertIn('href="/research-work-items">Open Research workbench', page)
        self.assertIn('href="/weekly-review">Open synthetic Weekly Review', page)
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
        self.assertEqual(page.count('data-value="missing_review_evidence"'), 8)
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

    def test_research_workbench_shows_redacted_nine_name_queue(self):
        status, headers, page = self.request("GET", "/research-work-items")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(page.count('data-work-item="true"'), 9)
        self.assertEqual(page.count('data-status="blocked"'), 9)
        for symbol in ("NVDA", "MU", "QCOM", "PLTR", "SPCX", "CRBS",
                       "QBTS", "RGTI", "AVGO"):
            self.assertIn(f'<th scope="row">{symbol}</th>', page)
        self.assertIn('<strong>0</strong> rights allowed', page)
        self.assertNotIn('<form', page)
        for excluded in ('source_uri', 'terms_uri', 'document_id', 'review_id',
                         'reviewer_reference', 'sha256', 'metric_value'):
            self.assertNotIn(excluded, page.lower())

    def test_research_workbench_shows_count_only_worksheet_readiness(self):
        status, _, page = self.request("GET", "/research-work-items")
        self.assertEqual(status, 200)
        self.assertIn('data-rights-worksheet-status="blocked"', page)
        self.assertIn('data-review-tasks="8"', page)
        self.assertIn('data-pending-reviews="8"', page)
        self.assertIn('data-required-checks="64"', page)
        self.assertIn('data-completed-checks="0"', page)
        self.assertIn('data-retrieval-status="disabled_separate_gate"', page)
        self.assertIn('data-release-authorized="false"', page)
        self.assertIn('8 of 8 reviews pending', page)
        self.assertIn('0 of 64 required checks complete', page)
        for private_field in ('source_uri', 'document_id', 'terms_uri',
                              'evidence_sha256', 'reviewer_reference',
                              'review_id'):
            self.assertNotIn(private_field, page.lower())

    def test_research_workbench_shows_redacted_capture_gate(self):
        status, _, page = self.request("GET", "/research-work-items")
        self.assertEqual(status, 200)
        self.assertIn('data-capture-gate-status="blocked"', page)
        self.assertIn('data-capture-candidates="8"', page)
        self.assertIn('data-rights-ready="0"', page)
        self.assertIn('data-capture-authorized="0"', page)
        self.assertIn('data-source-bytes-status="not_provided"', page)
        self.assertIn('data-capture-release-authorized="false"', page)
        self.assertIn('0 of 8 rights-ready', page)
        self.assertIn('0 of 8 capture-authorized', page)
        for private_field in ('authorization_id', 'document_id', 'source_uri',
                              'terms_uri', 'evidence_sha256',
                              'reviewer_reference'):
            self.assertNotIn(private_field, page.lower())

    def test_research_workbench_shows_ordered_public_m2_trace(self):
        trace = public_m2_acceptance_trace()
        self.assertEqual([stage['passed_count'] for stage in trace['stages']],
                         [8, 8, 0, 0, 0, 0])
        for path in RESEARCH_PATHS:
            with self.subTest(path=path):
                status, _, page = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn('data-m2-trace-status="blocked"', page)
                self.assertIn('data-m2-universe-count="9"', page)
                self.assertEqual(page.count('data-m2-gate="'), 6)
                self.assertIn('data-milestone-acceptance-recorded="false"', page)
                self.assertIn('data-m2-release-authorized="false"', page)
                self.assertIn('data-m2-gate="identity" data-gate-status="blocked" data-passed-count="8" data-blocked-count="1"', page)
                self.assertIn('data-m2-gate="metric_release" data-gate-status="blocked" data-passed-count="0" data-blocked-count="9"', page)
                for private_field in ('authorization_id', 'document_id',
                                      'source_uri', 'terms_uri', 'review_id',
                                      'reviewer_reference', 'sha256',
                                      'metric_value'):
                    self.assertNotIn(private_field, page.lower())

    def test_research_workbench_shows_synthetic_public_conformance_boundary(self):
        report = public_m2_synthetic_conformance()
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['public_source_state']['passed_counts'],
                         [8, 8, 0, 0, 0, 0])
        for path in RESEARCH_PATHS:
            with self.subTest(path=path):
                status, _, page = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn('data-m2-conformance-status="passed"', page)
                self.assertIn('data-synthetic-stage-count="6"', page)
                self.assertIn('data-synthetic-stages-passed="6"', page)
                self.assertIn('data-public-source-status="blocked"', page)
                self.assertIn('data-public-passed-counts="8,8,0,0,0,0"', page)
                self.assertIn('data-public-extraction-passed="0"', page)
                self.assertIn('data-public-metric-release-passed="0"', page)
                self.assertIn('data-conformance-acceptance-recorded="false"', page)
                self.assertIn('data-conformance-release-authorized="false"', page)
                self.assertIn('Synthetic path: 6 of 6 technical gates passed', page)
                for excluded in ('authorization_id', 'document_id',
                                 'observation_id', 'source_uri', 'terms_uri',
                                 'review_id', 'sha256', 'metric_id', '123.40'):
                    self.assertNotIn(excluded, page.lower())

    def test_research_workbench_filters_are_fixed_routes(self):
        expected = {
            "/research-work-items/identity": (1, "identity_unresolved"),
            "/research-work-items/source": (0, "source_candidate_missing"),
            "/research-work-items/rights": (8, "missing_review_evidence"),
        }
        for path, (count, blocker) in expected.items():
            with self.subTest(path=path):
                status, _, page = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(page.count('data-work-item="true"'), count)
                self.assertEqual(page.count(
                    f'data-primary-blocker="{blocker}"'), count)
        status, _, _ = self.request("GET", "/research-work-items?filter=rights")
        self.assertEqual(status, 404)
        with self.assertRaisesRegex(ValueError, 'invalid_research_workbench_filter'):
            render_research_work_items("../../.env")

    def test_weekly_review_renders_exact_typed_claim_sequence(self):
        status, headers, page = self.request("GET", "/weekly-review")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn('data-weekly-review-mode="synthetic"', page)
        self.assertIn('data-weekly-review-status="ready"', page)
        markers = [
            'data-weekly-section="observation"',
            'data-weekly-section="hypothesis"',
            'data-weekly-section="counterargument"',
            'data-weekly-section="missing_evidence"',
        ]
        self.assertEqual(page.count('data-weekly-section="'), 4)
        self.assertEqual(sorted(page.index(marker) for marker in markers),
                         [page.index(marker) for marker in markers])
        self.assertIn('data-evidence-status="synthetic_verified" '
                      'data-source-status="synthetic_fixture"', page)
        self.assertIn('data-evidence-status="unavailable" '
                      'data-source-status="missing"', page)
        self.assertIn('Period ending 2026-10-08', page)
        self.assertEqual(page, render_weekly_review())

    def test_weekly_review_is_readonly_synthetic_and_redacted(self):
        status, _, page = self.request("GET", "/weekly-review")
        self.assertEqual(status, 200)
        self.assertIn('data-investment-conclusion="false"', page)
        self.assertIn('data-milestone-acceptance-recorded="false"', page)
        self.assertIn('data-release-authorized="false"', page)
        for excluded in ('<form', '<input', '<button', 'statement_id',
                         'source_uri', 'document_id', 'review_id', 'sha256',
                         'metric_value', '"recommendation":', 'nvda', 'mu',
                         'qcom', 'pltr', 'spcx', 'crbs', 'qbts', 'rgti'):
            self.assertNotIn(excluded, page.lower())
        status, _, _ = self.request("GET", "/weekly-review?period=latest")
        self.assertEqual(status, 404)

    def test_weekly_review_shows_synthetic_ready_and_sourced_blocked(self):
        status, _, page = self.request("GET", "/weekly-review")
        self.assertEqual(status, 200)
        self.assertIn(
            'data-weekly-readiness-status="blocked_sourced_report"', page)
        self.assertIn('data-synthetic-shell-status="ready"', page)
        self.assertIn('data-synthetic-section-count="4"', page)
        self.assertIn('data-sourced-report-status="blocked"', page)
        self.assertIn('data-sourced-universe-count="9"', page)
        self.assertIn('data-sourced-passed-counts="8,8,0,0,0,0"', page)
        self.assertIn('data-sourced-statement-count="0"', page)
        self.assertIn('data-sourced-metric-count="0"', page)
        self.assertIn('Synthetic shell: ready', page)
        self.assertIn('Sourced report: blocked', page)

    def test_weekly_review_shows_count_only_source_manifest(self):
        status, _, page = self.request("GET", "/weekly-review")
        self.assertEqual(status, 200)
        self.assertIn('data-source-manifest-status="blocked"', page)
        self.assertIn('data-source-manifest-rule-count="4"', page)
        self.assertIn(
            'data-source-manifest-evidence-values="not_provided"', page)
        self.assertIn('data-source-manifest-complete-claims="0"', page)
        self.assertIn('data-actual-report-eligible="false"', page)
        self.assertEqual(page.count('data-manifest-section="'), 4)
        self.assertEqual(page.count('data-complete-claims="0"'), 4)
        self.assertIn('data-required-fields="8"', page)
        self.assertEqual(page.count('data-required-fields="5"'), 3)
        for excluded in ('claim_id', 'instrument_id', 'source_document_id',
                         'observation_id', 'rights_decision',
                         'assumption_label', 'supporting_claim_ids',
                         'challenged_claim_ids', 'gap_code'):
            self.assertNotIn(excluded, page)

    def test_weekly_review_projects_count_only_claim_receipt(self):
        status, _, page = self.request("GET", "/weekly-review")
        self.assertEqual(status, 200)
        self.assertIn('data-claim-receipt-status="blocked"', page)
        self.assertIn('data-claim-receipt-required-fields="23"', page)
        self.assertIn('data-claim-receipt-provided-fields="13"', page)
        self.assertIn('data-claim-receipt-missing-fields="10"', page)
        self.assertIn('data-claim-receipt-synthetic-complete="1"', page)
        self.assertIn('data-claim-receipt-blocked="3"', page)
        self.assertIn(
            'data-claim-receipt-evidence-values="not_accepted"', page)
        self.assertEqual(page.count('data-provided-fields="'), 4)
        self.assertEqual(page.count('data-missing-fields="'), 4)
        self.assertIn('data-provided-fields="8" data-missing-fields="0" '
                      'data-binding-status="synthetic_fields_complete"', page)
        self.assertEqual(page.count('data-complete-claims="0"'), 4)
        self.assertIn('Presence counts show structure only', page)
        for excluded in ('claim_id', 'instrument_id', 'source_document_id',
                         'observation_id', 'rights_decision',
                         'assumption_label', 'supporting_claim_ids',
                         'challenged_claim_ids', 'gap_code'):
            self.assertNotIn(excluded, page)
