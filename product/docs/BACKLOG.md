# Backlog and decision register

Priority order is dependency-driven. GitHub issue links will accompany the launch PR.

| ID | Work item | Priority | Due | Owner role | Exit |
|---|---|---|---|---|---|
| SEC-01 | Review inherited tracked .env privately; rotate if needed | P0 | Sep 13 | Founder/security | Review recorded without exposing values |
| ENG-01 | Foundation CI and CLI error-path tests | P0 | Sep 19 | Engineering/QA | CI on exact commit; tests and demo pass |
| UX-01 | Clickable synthetic screen prototype for founder feedback | P0 | Sep 19 | Product/application | Navigation and sample workflows usable; no live data implied |
| DAT-01 | Redacted Fidelity sample and import contract | P0 | Sep 19 | Founder/data | Format and cash/core semantics resolved |
| DAT-02 | Import/reconciliation implementation | P0 | Oct 3 | Data/QA | All rows accounted; duplicate/unsupported cases explicit |
| RES-01 | Security master, CRBS identity and provider rights | P0 | Oct 3 | Research/data | Stable IDs and licensed access plan |
| RES-02 | Sourced weekly report and macro vintage handling | P1 | Oct 17 | Research | Facts, assumptions and dates distinguishable |
| QNT-01 | Baselines and chronological evaluation | P1 | Oct 31 | Quant/QA | Holdout and transaction-cost evidence |
| OPT-01 | Chain adapters, portfolio reservations and assignment scenarios | P1 | Oct 31 | Quant/integration | No double-use of cash/shares; stale chain blocks ranking |
| APP-01 | Private UI, access and jobs | P1 | Nov 14 | Application/security | End-to-end and isolation tests |
| REL-01 | Hardening, restore, UAT and investor demo | P1 | Dec 12 | QA/ops/founder | Documented acceptance |

## Decisions for founder

| Decision | Recommendation | Status |
|---|---|---|
| Product boundary | December read-only/paper prototype; separate real-money gate | Proposed for approval |
| Code destination | Use isolated product/ branch in existing quant repo; private repo before sensitive commercial work | Provisional; no sensitive data committed |
| Risk objective | Evaluate net total return and drawdown versus agreed benchmark; premium is secondary | Needs customer mandate |
| Budget | Spend $0 until provider and reviewer quotes are reviewed | Default pending approval |
| Customer input | Redacted Fidelity export, account aliases, all asset rows retained | Requested |
| Symbol ambiguity | Confirm CRBS issuer; verify SPCX via primary source | Open |

## Next concrete increment

September 15 afternoon: connected the five-area overview, interactive put form and read-only phase checklist through exact allowlisted local routes. HTTP tests verify round-trip links and rejection of arbitrary file/query paths. UX-01 remains pending browser/device QA and founder feedback. Next bounded backend priority: metric definitions (units, currency, period, null policy and transformation compatibility); do not count blocked visual QA as completed.

September 14 afternoon: UX-01 first slice implemented as an offline five-area HTML preview with expandable arithmetic, failure-state and option-risk examples. Displayed values are now bound to a fixed risk-kernel model by regression tests. Browser/device verification and founder validation remain pending; local and cloud browser routes were unavailable in the current runtime. Next: browser QA in a capable environment and founder feedback, followed by kernel-backed editable scenarios. R13 remains planned, not delivered by the preview.

September 14: the normalized-source/replay path, effective-dated identity, use-specific rights, point-in-time observation selection and combined research-input gate are implemented with synthetic tests. R04, R06 and R15 remain partial: Fidelity mapping, production persistence, populated evidence, actual license review, metric registry and experiment registry are pending.

Founder steering, September 14: prioritize a clickable synthetic screen prototype by September 19 and product-oriented briefings showing what can be tried. See product/README.md for screen concepts and the preview timeline. The metric-definition registry covering units, currency, period, null policy and transformation compatibility follows as a backend dependency. Fidelity mapping remains dependent on a redacted representative sample. Continue useful work without repeatedly asking for the same approval.

September 15 morning: added the first editable kernel-backed UX slice—a localhost-only, non-persistent cash-secured-put expiration form with fail-closed validation and HTTP security/integration tests. UX-01 remains partial until browser/device QA and founder workflow validation. Next: integrate the local Options Lab into the five-area navigation and complete browser/accessibility checks; metric registry remains the next financial-data foundation.
