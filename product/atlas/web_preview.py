"""Local-only synthetic Options Lab preview.

This server has no account, market-data, persistence, recommendation or order
capability. It exists only to let the founder exercise the deterministic expiry
payoff kernel through a browser form.
"""
from hmac import compare_digest
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from secrets import token_urlsafe
from urllib.parse import parse_qs
from decimal import Decimal

from .risk import standard_option_payoff


MAX_BODY_BYTES = 2_048
FIELDS = ("strike", "premium_per_share", "terminal_price", "fees", "available_cash")
DEFAULTS = {"strike": "50", "premium_per_share": "2", "terminal_price": "48",
            "fees": "0", "available_cash": "5000"}


def _money(value):
    number = Decimal(value)
    sign = "-" if number < 0 else ""
    return f"{sign}${abs(number)}"


def calculate_put(values):
    """Calculate one standard synthetic CSP after strict single-value parsing."""
    if set(values) != set(FIELDS):
        raise ValueError("Scenario field set is invalid")
    parsed = {}
    for name in FIELDS:
        candidates = values.get(name)
        if not isinstance(candidates, list) or len(candidates) != 1:
            raise ValueError("Every scenario field must occur exactly once")
        value = candidates[0]
        if not isinstance(value, str) or not value or len(value) > 32:
            raise ValueError("Scenario values must be short decimal strings")
        parsed[name] = value
    return parsed, standard_option_payoff(
        strategy="cash_secured_put", contracts=1, **parsed)


def render_page(*, token, values=None, result=None, error=None):
    values = values or DEFAULTS
    safe = {key: escape(str(values.get(key, DEFAULTS[key])), quote=True) for key in FIELDS}
    if result:
        panel = f"""<section class="result" aria-live="polite"><h2>Expiration result</h2>
<dl><dt>Modeled P&amp;L</dt><dd>{escape(_money(result['expiration_pnl']))}</dd>
<dt>Maximum modeled loss</dt><dd>{escape(_money(result['maximum_loss']))}</dd>
<dt>Maximum modeled gain</dt><dd>{escape(_money(result['maximum_pnl']))}</dd>
<dt>Breakeven</dt><dd>{escape(_money(result['breakeven']))}</dd>
<dt>Gross cash required</dt><dd>{escape(_money(result['required_cash']))}</dd></dl></section>"""
    elif error:
        panel = f'<p class="error" role="alert">Scenario blocked: {escape(error)}</p>'
    else:
        panel = '<p class="notice">Change the synthetic inputs, then calculate.</p>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas Options Lab · Synthetic</title>
<style>:root{{font:16px/1.5 system-ui;color:#183244;background:#edf3f5}}*{{box-sizing:border-box}}body{{margin:0}}header{{background:#112e40;color:#fff;padding:24px}}main{{max-width:760px;margin:auto;padding:24px}}form,.result,.notice,.error{{background:#fff;border:1px solid #c4d5dc;border-radius:12px;padding:22px;margin:18px 0}}label{{display:block;font-weight:650;margin-top:12px}}input{{width:100%;font:inherit;padding:10px;border:1px solid #708b98;border-radius:6px}}button{{margin-top:20px;background:#076278;color:#fff;border:0;border-radius:7px;padding:12px 18px;font:inherit;font-weight:700}}dt{{color:#526d79}}dd{{font-size:1.3rem;font-weight:700;margin:0 0 10px}}.banner{{background:#fff0c4;color:#513800;padding:10px 24px}}.error{{border-left:5px solid #a34400}}small{{display:block;color:#526d79;margin-top:16px}}:focus-visible{{outline:3px solid #bf6400;outline-offset:3px}}</style></head>
<body><header><strong>ATLAS</strong><h1>Options Lab</h1><p>Interactive expiration scenario</p></header>
<div class="banner"><strong>Synthetic inputs only.</strong> Local calculation—not a quote, forecast, recommendation or order.</div>
<main>{panel}<form method="post" action="/calculate"><input type="hidden" name="token" value="{escape(token, quote=True)}">
<label for="strike">Put strike per share ($)</label><input id="strike" name="strike" inputmode="decimal" value="{safe['strike']}" required>
<label for="premium">Premium received per share ($)</label><input id="premium" name="premium_per_share" inputmode="decimal" value="{safe['premium_per_share']}" required>
<label for="terminal">Underlying price at expiration ($)</label><input id="terminal" name="terminal_price" inputmode="decimal" value="{safe['terminal_price']}" required>
<label for="fees">Total fees ($)</label><input id="fees" name="fees" inputmode="decimal" value="{safe['fees']}" required>
<label for="cash">Available cash ($)</label><input id="cash" name="available_cash" inputmode="decimal" value="{safe['available_cash']}" required>
<button type="submit">Calculate one-contract scenario</button><small>One standard 100-share cash-secured put. Required cash is strike × 100 + fees; premium is not counted as available collateral.</small></form>
<p><strong>Important:</strong> expiration-only math omits early assignment, dividends, taxes, interest, bid/ask spread, liquidity and changing volatility. Nothing is saved.</p></main></body></html>"""


def make_handler(token):
    class PreviewHandler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            return

        def _send(self, status, page):
            encoded = page.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(encoded)

        def _valid_host(self):
            host = self.headers.get("Host", "").split(":", 1)[0]
            return host in {"127.0.0.1", "localhost"}

        def do_GET(self):
            if not self._valid_host() or self.path != "/":
                self._send(404, render_page(token=token, error="Page not found"))
                return
            self._send(200, render_page(token=token))

        def do_POST(self):
            if not self._valid_host() or self.path != "/calculate":
                self._send(404, render_page(token=token, error="Page not found"))
                return
            if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self._send(415, render_page(token=token, error="Unsupported request type"))
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                self._send(413, render_page(token=token, error="Request is too large"))
                return
            try:
                form = parse_qs(self.rfile.read(length).decode("utf-8", "strict"),
                                keep_blank_values=True, max_num_fields=12)
            except (UnicodeError, ValueError):
                self._send(400, render_page(token=token, error="Request could not be read"))
                return
            submitted = form.pop("token", [])
            display = {key: (items[0] if len(items) == 1 else "")
                       for key, items in form.items() if key in FIELDS}
            if len(submitted) != 1 or not compare_digest(submitted[0], token):
                self._send(403, render_page(token=token, values=display,
                                             error="Session token is invalid; reload the page"))
                return
            try:
                values, result = calculate_put(form)
            except (ValueError, KeyError, TypeError, UnicodeError):
                self._send(400, render_page(token=token, values=display,
                                             error="Check the decimal inputs and cash collateral"))
                return
            self._send(200, render_page(token=token, values=values, result=result))

    return PreviewHandler


def serve_preview(port=8765):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("Preview port must be between 1024 and 65535")
    server = HTTPServer(("127.0.0.1", port), make_handler(token_urlsafe(32)))
    print(f"Atlas synthetic preview: http://127.0.0.1:{server.server_port}/")
    print("Press Ctrl+C to stop. No data is saved.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
