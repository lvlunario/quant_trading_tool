# Offline founder preview — UX-01

Open `index.html` locally in a desktop browser. No server, dependencies, login or uploads are required. The page uses native links and expandable disclosures, with no JavaScript, remote assets or persistence. It is a fixed synthetic interaction prototype, not R13's private application and not a live calculation UI. Its checked-in portfolio and option values are regression-tested against `atlas.risk`; changing either the kernel or displayed values inconsistently fails the test suite.

## Five-minute validation

1. Click Overview, Portfolio, Research, Options Lab and Weekly Review. Expected: the corresponding section comes into view.
2. In Portfolio, expand the arithmetic. Expected: $5,000 equity + $5,000 cash = $10,000; concentration 50%.
3. Expand the incomplete-import warning. Expected: visibly blocked analysis, explicitly labeled as illustrative rather than an actual import result.
4. Click DEMO to inspect Research. Expected: missing evidence, no fabricated thesis and CRBS unresolved.
5. Expand all three put outcomes. Expected at underlying prices $0 / $48 / $60: expiration P&L −$4,800 / $0 / $200, using the displayed assumptions.
6. Use keyboard Tab and Enter to navigate, and Enter/Space to toggle disclosures. At phone width verify text remains readable without page-wide horizontal scrolling.
7. Report the screen/task, expected versus observed behavior and confusing wording here in the project discussion. Use synthetic screenshots only. No acceptance is recorded automatically.

Automated Python tests check navigation targets, labels, disclosure structure, absence of scripts/forms/remote links and exact equality between displayed financial values and the fixed kernel model. They do not execute a browser, verify rendering, audit accessibility or provide runtime financial interaction. Browser QA results and limitations belong in the daily log.

Not implemented: editable scenarios, kernel integration, current data, Fidelity import UI, customer storage, authentication, saved journal, live trade comparisons or orders. All phase decisions remain pending. Next: browser/device QA and a kernel-backed synthetic scenario slice after design review.
