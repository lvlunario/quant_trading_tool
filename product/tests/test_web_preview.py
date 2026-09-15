from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread
from urllib.parse import urlencode
import unittest

from atlas.web_preview import calculate_put, make_handler, render_page, serve_preview


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
