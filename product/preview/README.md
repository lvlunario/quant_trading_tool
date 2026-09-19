# Offline founder preview — UX-01

Open `index.html` locally in a desktop browser. No server, dependencies, login or uploads are required. The page uses native links and expandable disclosures, with no JavaScript, remote assets or persistence. It is a fixed synthetic interaction prototype, not R13's private application and not a live calculation UI. Its checked-in portfolio and option values are regression-tested against `atlas.risk`; changing either the kernel or displayed values inconsistently fails the test suite.

## Five-minute validation

1. Click Overview, Portfolio, Research, Options Lab and Weekly Review. Expected: the corresponding section comes into view.
2. In Portfolio, expand the arithmetic. Expected: $5,000 equity + $5,000 cash = $10,000; concentration 50%.
3. Expand the incomplete-import warning. Expected: visibly blocked analysis, explicitly labeled as illustrative rather than an actual import result.
4. Click DEMO to inspect Research. Expected: an invented $123.40 quarterly metric shows its unit, reporting dates, availability time and transformation. Expand its trace, then read why real research remains blocked and CRBS unresolved.
5. Expand all three put outcomes. Expected at underlying prices $0 / $48 / $60: expiration P&L −$4,800 / $0 / $200, using the displayed assumptions.
6. Use keyboard Tab and Enter to navigate, and Enter/Space to toggle disclosures. At phone width verify text remains readable without page-wide horizontal scrolling.
7. Report the screen/task, expected versus observed behavior and confusing wording here in the project discussion. Use synthetic screenshots only. No acceptance is recorded automatically.

Automated Python tests check navigation targets, labels, disclosure structure, absence of scripts/forms/remote links and exact equality between displayed portfolio, option and research-trace values and the fixed kernel models. They do not execute a browser, verify rendering or audit accessibility. Browser QA results and limitations belong in the daily log.

Not implemented in this fixed page: editable scenarios, runtime kernel integration, current data, Fidelity import UI, customer storage, authentication, saved journal, live trade comparisons or orders. All phase decisions remain pending.

## Interactive Options Lab slice

From the `product` directory, run `python -m atlas --preview-server`, then open the displayed localhost address. You may edit the five synthetic cash-secured-put inputs. The Python kernel returns expiration P&L, modeled maximum loss/gain, breakeven and gross collateral. Invalid decimal inputs, insufficient cash and invalid session tokens fail closed. Nothing is saved and the server accepts connections only on `127.0.0.1`. Stop it with Ctrl+C.

The local server starts at `/overview`, serving the fixed five-area page with a link from Options Lab to the interactive form at `/`. The form links back to the overview. Weekly Review opens the phase checklist at `/checklist`, displayed as read-only text with no approval form. Only these exact routes are served; this is not a general file server. Current chains, covered-call interaction, accounts, research, persistence, login and orders remain unavailable.

For founder validation: navigate to Options Lab, calculate a synthetic scenario, return to Portfolio, then open the checklist from Weekly Review. Expected: working round-trip links and no saved decisions. HTTP route/content tests pass; visual, keyboard and phone-browser behavior still require device QA.
