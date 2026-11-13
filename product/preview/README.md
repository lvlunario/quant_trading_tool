# Offline founder preview — UX-01

Open `index.html` locally in a desktop browser. No server, dependencies, login or uploads are required. The page uses native links and expandable disclosures, with no JavaScript, remote assets or persistence. It is a fixed synthetic interaction prototype, not R13's private application and not a live calculation UI. Its checked-in portfolio and option values are regression-tested against `atlas.risk`; changing either the kernel or displayed values inconsistently fails the test suite.

## Five-minute validation

1. Click Overview, Portfolio, Research, Options Lab and Weekly Review. Expected: the corresponding section comes into view.
2. In Portfolio, expand the arithmetic. Expected: $5,000 equity + $5,000 cash = $10,000; concentration 50%.
3. Inspect the four import receipt states. Expected: eligible, blocked, duplicate and replay-check-required examples show only row counts and state; no holdings or account details. Expand the incomplete-import warning and confirm it is illustrative rather than an actual import result.
4. Click DEMO to inspect Research. Expected: an invented $123.40 quarterly metric shows its unit, reporting dates, availability time and transformation. Inspect the exact synthetic document/provider/dataset binding; verify NVDA, MU and AVGO each show `missing_review_evidence`, retrieval disabled and release unauthorized; inspect the blocked real-provider qualification state; then compare the original 100.0 macro release, the revised 99.5 value and the explicit `macro_not_yet_available` state. Read why real research remains blocked and CRBS unresolved.
5. Expand all three put outcomes. Expected at underlying prices $0 / $48 / $60: expiration P&L −$4,800 / $0 / $200, using the displayed assumptions.
6. Use keyboard Tab and Enter to navigate, and Enter/Space to toggle disclosures. At phone width verify text remains readable without page-wide horizontal scrolling.
7. Report the screen/task, expected versus observed behavior and confusing wording here in the project discussion. Use synthetic screenshots only. No acceptance is recorded automatically.

Automated Python tests check navigation targets, labels, disclosure structure, absence of scripts/forms/remote links and exact equality between displayed portfolio, option, source-binding, reviewed-rights, provider-qualification and macro-vintage values and their backend contracts. They do not execute a browser, verify rendering or audit accessibility. Browser QA results and limitations belong in the daily log.

Not implemented in this fixed page: editable scenarios, current data, Fidelity import UI, customer storage, authentication, saved journal, live trade comparisons or orders. Its receipt examples are generated from the backend presentation contract during regression testing, but the HTML does not accept files or run an import. Routine best-practice decisions are delegated; sensitive-data transfer and production-impacting actions still require explicit authorization.

## Interactive Options Lab slice

From the `product` directory, run `python -m atlas --preview-server`, then open the displayed localhost address. You may edit the five synthetic cash-secured-put inputs. The Python kernel returns expiration P&L, modeled maximum loss/gain, breakeven and gross collateral. Invalid decimal inputs, insufficient cash and invalid session tokens fail closed. Nothing is saved and the server accepts connections only on `127.0.0.1`. Stop it with Ctrl+C.

The local server starts at `/overview`, serving the fixed five-area page with links to the interactive Options Lab at `/`, the fixed synthetic import workflow at `/import-demo`, and the M1 evidence boundary at `/m1-status`. The import page processes only the checked-in invented CSV through the real parser, reconciliation and receipt path; it has no upload control, accepts no path and saves nothing. The M1 page separates verified synthetic checks from Fidelity-specific evidence gaps and records no approval. The Options form links back to the overview. Weekly Review opens the phase checklist at `/checklist`, displayed as read-only text with no approval form. Only these exact routes are served; this is not a general file server. Current chains, customer accounts, real broker imports, persistence, login and orders remain unavailable.

For founder validation: navigate to Portfolio, open the fixed synthetic import demo and verify its replay-check-required receipt, then open M1 conformance and confirm the four verified-synthetic, four external-evidence-blocked and one not-implemented checks. Return to Options Lab, calculate a synthetic scenario, then open the checklist from Weekly Review. Expected: working round-trip links, no upload field and no saved data, approvals or decisions. HTTP route/content tests pass; visual, keyboard and phone-browser behavior still require device QA.
