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
from datetime import datetime, timezone
from pathlib import Path

from .conformance import m1_import_conformance, recommend_m1_disposition
from .import_workflow import synthetic_csv_report
from .research_work_items import compose_research_work_queue
from .rights_evidence import (assess_reviewed_rights,
                              load_reviewed_rights_evidence)
from .risk import standard_option_payoff
from .source_catalog import load_public_source_catalog
from .watchlist_registry import load_public_watchlist_registry


MAX_BODY_BYTES = 2_048
FIELDS = ("strike", "premium_per_share", "terminal_price", "fees", "available_cash")
DEFAULTS = {"strike": "50", "premium_per_share": "2", "terminal_price": "48",
            "fees": "0", "available_cash": "5000"}
WORKBENCH_AS_OF = datetime(2026, 10, 5, tzinfo=timezone.utc)
RESEARCH_ROUTE_FILTERS = {
    "/research-work-items": "all",
    "/research-work-items/identity": "identity_unresolved",
    "/research-work-items/source": "source_candidate_missing",
    "/research-work-items/rights": "missing_review_evidence",
}


def render_overview():
    """Serve only the fixed synthetic page, never a caller-selected file."""
    page = (Path(__file__).resolve().parents[1] / "preview/index.html").read_text()
    return page.replace("<!-- interactive-options-link -->",
                        '<p><a href="/">Open interactive Options Lab →</a></p>').replace(
        "<!-- interactive-import-link -->",
        '<p><a href="/import-demo">Run fixed synthetic import demo →</a> · '
        '<a href="/m1-status">View M1 conformance →</a></p>').replace(
        "<!-- interactive-research-work-items-link -->",
        '<p><a href="/research-work-items">Open Research workbench →</a></p>').replace(
        '../docs/PROGRAM.md#founder-phase-acceptance-checklist', '/checklist')


def public_research_work_queue():
    """Build the checked-in public-safe queue at a fixed evidence cutoff."""
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    registry = load_public_watchlist_registry(
        (fixtures / "public-watchlist-identities.json").read_bytes(),
        now=WORKBENCH_AS_OF)
    catalog = load_public_source_catalog(
        (fixtures / "public-research-sources.json").read_bytes(), registry,
        now=WORKBENCH_AS_OF)
    evidence = load_reviewed_rights_evidence(
        (fixtures / "public-source-rights-evidence.json").read_bytes(), catalog,
        now=WORKBENCH_AS_OF)
    rights = assess_reviewed_rights(catalog, evidence, at=WORKBENCH_AS_OF)
    return compose_research_work_queue(registry, catalog, rights).public_summary()


def render_research_work_items(filter_code="all"):
    """Render a redacted work queue selected only by a fixed route mapping."""
    allowed = frozenset(RESEARCH_ROUTE_FILTERS.values())
    if filter_code not in allowed:
        raise ValueError("invalid_research_workbench_filter")
    report = public_research_work_queue()
    items = report["items"]
    if filter_code != "all":
        items = [item for item in items
                 if item["primary_blocker"] == filter_code]
    filter_labels = {
        "all": "All blocked work",
        "identity_unresolved": "Identity",
        "source_candidate_missing": "Source candidate",
        "missing_review_evidence": "Rights review",
    }
    route_for = {value: route for route, value in RESEARCH_ROUTE_FILTERS.items()}
    nav = " · ".join(
        f'<a href="{escape(route_for[code], quote=True)}"'
        f'{" aria-current=\"page\"" if code == filter_code else ""}>'
        f'{escape(label)}</a>'
        for code, label in filter_labels.items())
    rows = "".join(
        '<tr data-work-item="true" data-primary-blocker="{blocker}" '
        'data-status="{status}"><th scope="row">{symbol}</th>'
        '<td>{identity}</td><td>{source}</td><td>{rights}</td>'
        '<td>{blocker_label}</td><td>{action}</td></tr>'.format(
            blocker=escape(item["primary_blocker"], quote=True),
            status=escape(item["status"], quote=True),
            symbol=escape(item["symbol"]),
            identity=escape(item["identity_status"].replace("_", " ").title()),
            source=escape(item["source_status"].replace("_", " ").title()),
            rights=escape(item["rights_status"].replace("_", " ").title()),
            blocker_label=escape(item["primary_blocker"].replace("_", " ").title()),
            action=escape(item["next_action"].replace("_", " ").title()))
        for item in items)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas Research Workbench</title>
<style>:root{{font:15px/1.5 system-ui;color:#183244;background:#edf3f5}}body{{max-width:1180px;margin:auto;padding:24px}}.summary{{display:flex;gap:12px;flex-wrap:wrap}}.summary span{{background:#fff;border:1px solid #c4d5dc;border-radius:9px;padding:12px}}nav{{margin:18px 0}}table{{border-collapse:collapse;width:100%;background:#fff}}th,td{{text-align:left;vertical-align:top;padding:10px;border:1px solid #cad8de}}thead{{background:#dfecee}}.warning{{background:#fff0c4;padding:12px}}:focus-visible{{outline:3px solid #bf6400;outline-offset:3px}}</style></head>
<body data-workbench-filter="{escape(filter_code, quote=True)}"><a href="/overview">Return to five-area overview</a>
<h1>Research workbench</h1><p class="warning"><strong>Workflow status only.</strong> No source bytes, metric values, recommendations, holdings or release authority.</p>
<div class="summary"><span><strong>{report['work_item_count']}</strong> total work items</span><span><strong>{report['blocked_count']}</strong> blocked</span><span><strong>{report['catalogued_source_count']}</strong> source candidates</span><span><strong>{report['rights_allowed_count']}</strong> rights allowed</span><span><strong>{len(items)}</strong> shown</span></div>
<nav aria-label="Research work filters">{nav}</nav><h2>{escape(filter_labels[filter_code])}</h2>
<div style="overflow-x:auto"><table><thead><tr><th>Symbol</th><th>Identity</th><th>Source</th><th>Rights</th><th>Earliest blocker</th><th>Controlled next action</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Extraction remains unattempted, every metric remains unavailable, technical retrieval is disabled and release is unauthorized.</p>
<p>Filters are fixed server routes. This page has no query input, upload, network retrieval or persistence.</p></body></html>'''


def render_import_demo():
    """Run only the checked-in invented fixture and show its redacted receipt."""
    fixture = (Path(__file__).resolve().parents[1] /
               "fixtures/synthetic-broker.csv").read_bytes()
    report = synthetic_csv_report(fixture)
    receipt = report['receipt']
    if receipt['mode'] != 'synthetic':
        raise AssertionError('import_demo_must_be_synthetic')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas Import Demo · Synthetic</title>
<style>:root{{font:16px/1.5 system-ui;color:#183244;background:#edf3f5}}body{{max-width:760px;margin:auto;padding:24px}}section{{background:#fff;border:1px solid #c4d5dc;border-radius:12px;padding:22px;margin:18px 0}}dt{{color:#526d79}}dd{{font-size:1.2rem;font-weight:700;margin:0 0 10px}}.banner{{background:#fff0c4;padding:12px}}:focus-visible{{outline:3px solid #bf6400;outline-offset:3px}}</style></head>
<body><a href="/overview">Return to five-area overview</a> · <a href="/m1-status">View M1 conformance</a><h1>Synthetic import demo</h1>
<p class="banner"><strong>Checked-in invented fixture only.</strong> No upload, account connection, file picker, saved portfolio or order capability.</p>
<section data-import-decision="{escape(receipt['decision'], quote=True)}"
 data-reconciliation="{escape(receipt['reconciliation'], quote=True)}"
 data-replay="{escape(receipt['replay'], quote=True)}"
 data-input-rows="{receipt['input_rows']}" data-rejected-rows="{receipt['rejected_rows']}"
 data-publishable-rows="{receipt['publishable_rows']}"><h2>Import receipt</h2><dl>
<dt>Decision</dt><dd>{escape(receipt['decision'].replace('_', ' ').title())}</dd>
<dt>Reconciliation</dt><dd>{escape(receipt['reconciliation'].title())}</dd>
<dt>Replay status</dt><dd>{escape(receipt['replay'].replace('_', ' ').title())}</dd>
<dt>Rows</dt><dd>{receipt['input_rows']} input · {receipt['rejected_rows']} rejected · {receipt['publishable_rows']} provisionally publishable</dd>
<dt>Parser</dt><dd>{escape(report['parser_contract'])}</dd></dl></section>
<p><strong>Why publication is not yet eligible:</strong> this read-only demonstration uses no private replay ledger, so an identical retry cannot be durably suppressed. It calculates a receipt but persists nothing.</p>
<p>No symbols, quantities, prices, account aliases, totals, source path or source hash are displayed.</p></body></html>'''


def render_m1_status():
    """Render the public-safe M1 evidence boundary; record no approval."""
    report = m1_import_conformance()
    disposition = recommend_m1_disposition(report)
    rows = ''.join(
        '<tr data-check-id="{check_id}" data-status="{status}">'
        '<th scope="row">{capability}</th><td>{status_label}</td>'
        '<td>{evidence}</td><td>{limitation}</td></tr>'.format(
            check_id=escape(check['check_id'], quote=True),
            status=escape(check['status'], quote=True),
            capability=escape(check['capability']),
            status_label=escape(check['status'].replace('_', ' ').title()),
            evidence=escape(check['evidence']),
            limitation=escape(check['limitation']))
        for check in report['checks'])
    counts = report['counts']
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas M1 Conformance</title>
<style>:root{{font:15px/1.5 system-ui;color:#183244;background:#edf3f5}}body{{max-width:1100px;margin:auto;padding:24px}}.summary{{display:flex;gap:12px;flex-wrap:wrap}}.summary span{{background:#fff;border:1px solid #c4d5dc;border-radius:9px;padding:12px}}table{{border-collapse:collapse;width:100%;background:#fff;margin-top:18px}}th,td{{text-align:left;vertical-align:top;padding:10px;border:1px solid #cad8de}}thead{{background:#dfecee}}.warning{{background:#fff0c4;padding:12px}}:focus-visible{{outline:3px solid #bf6400;outline-offset:3px}}</style></head>
<body><a href="/overview">Return to five-area overview</a> · <a href="/import-demo">Run synthetic import demo</a>
<h1>M1 Portfolio Truth conformance</h1><p>Milestone: {escape(report['milestone_date'])}. Overall status: <strong>{escape(report['overall_status'].replace('_', ' ').title())}</strong>.</p>
<div class="summary"><span><strong>{counts['verified_synthetic']}</strong> verified with synthetic evidence</span><span><strong>{counts['blocked_external_evidence']}</strong> blocked on external evidence</span><span><strong>{counts['not_implemented']}</strong> not implemented</span></div>
<p class="warning"><strong>Scope boundary:</strong> this is an engineering conformance statement, not founder approval, Fidelity compatibility, browser acceptance or release authorization.</p>
<div style="overflow-x:auto"><table><thead><tr><th>Capability</th><th>Status</th><th>Evidence</th><th>Limitation</th></tr></thead><tbody>{rows}</tbody></table></div>
<section data-synthetic-disposition="{escape(disposition['synthetic_scope'], quote=True)}" data-fidelity-disposition="{escape(disposition['fidelity_scope'], quote=True)}" data-phase-progression="{escape(disposition['phase_progression'], quote=True)}"><h2>Engineering recommendation for October 3</h2><ul><li>Accept the documented synthetic engineering evidence only.</li><li>Defer Fidelity-specific validation until the private boundary, authorized export and source-specific reconciliation evidence exist.</li><li>Continue the synthetic/manual-redacted fallback without moving the conditional December target.</li></ul><p><strong>No founder approval or release authorization is recorded.</strong></p></section>
<p>No personal portfolio or broker-export content is used or displayed.</p></body></html>'''


def render_checklist():
    manual = (Path(__file__).resolve().parents[1] / "docs/PROGRAM.md").read_text()
    checklist = manual.split("## Founder phase acceptance checklist", 1)[1]
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Atlas founder checklist</title><style>body{font:16px/1.5 system-ui;'
            'max-width:900px;margin:auto;padding:24px}pre{white-space:pre-wrap}</style>'
            '<a href="/overview">Return to synthetic overview</a>'
            '<h1>Founder phase acceptance checklist</h1><p>Read-only manual; '
            'no decisions are saved or approved here.</p><pre>' + escape(checklist) + '</pre></html>')


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
<body><header><strong>ATLAS</strong><h1>Options Lab</h1><p>Interactive expiration scenario</p><a href="/overview" style="color:white">Return to five-area overview</a></header>
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
            if not self._valid_host() or self.path not in {
                    "/", "/overview", "/checklist", "/import-demo", "/m1-status",
                    *RESEARCH_ROUTE_FILTERS}:
                self._send(404, render_page(token=token, error="Page not found"))
                return
            if self.path == "/overview":
                self._send(200, render_overview())
            elif self.path == "/checklist":
                self._send(200, render_checklist())
            elif self.path == "/import-demo":
                self._send(200, render_import_demo())
            elif self.path == "/m1-status":
                self._send(200, render_m1_status())
            elif self.path in RESEARCH_ROUTE_FILTERS:
                self._send(200, render_research_work_items(
                    RESEARCH_ROUTE_FILTERS[self.path]))
            else:
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
    print(f"Atlas synthetic preview: http://127.0.0.1:{server.server_port}/overview")
    print("Press Ctrl+C to stop. No data is saved.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
