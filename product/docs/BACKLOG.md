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

## Current delegated decisions

See [September 22 delegated decisions](PROGRAM.md#delegated-project-decisions--september-22-2026). These supersede earlier pending entries for product scope, synthetic fallback and destination policy. M0 engineering baseline is conditionally accepted for progression; browser and usability evidence remain open. A representative export and private environment-file review remain unavailable inputs, not repeated requests for routine permission.

## Historical decision proposals

| Decision | Recommendation | Status |
|---|---|---|
| Product boundary | December read-only/paper prototype; separate real-money gate | Adopted under delegated authority, Sep 22 |
| Code destination | Use isolated product/ branch in existing quant repo; private repo before sensitive commercial work | Separate private destination selected; not provisioned; current public work stays synthetic |
| Risk objective | Evaluate net total return and drawdown versus agreed benchmark; premium is secondary | Needs customer mandate |
| Budget | Spend $0 until provider and reviewer quotes are reviewed | $0 adopted under delegated authority, Sep 22 |
| Customer input | Redacted Fidelity export, account aliases, all asset rows retained | Requested |
| Symbol ambiguity | Confirm CRBS issuer; verify SPCX via primary source | Open |

## Next concrete increment

September 22 afternoon: added a versioned minimal receipt to both import CLI paths, with controlled decisions, row counts and no financial/account fields. Inconsistent publication states are rejected. Next: display synthetic receipts on the Portfolio preview and verify browser behavior. Routine decisions follow the September 22 delegation.

September 22 morning: extended the private hash-only replay receipt to the synthetic CSV command. The first attempt records source identity, exact-byte digest, outcome and time; an identical retry returns zero publishable rows. No holdings enter the ledger. Next: define a redacted import receipt schema that separates source, validation, reconciliation and replay decisions for UI/report consumption.

September 21 evening: exposed the bounded parser as `--synthetic-csv-demo` with a checked-in invented fixture, exact-byte SHA-256 provenance, opaque source identity, redacted summary output and exit code 3 for blocked reconciliations. The demo uses its runtime as a synthetic source time and is not Fidelity validation. Next: add a private hash-only replay receipt to the synthetic CSV workflow so retries cannot republish rows.

September 21 afternoon: added a bounded internal synthetic CSV parser. It enforces UTF-8/1 MB/10,000-record limits, exact profile headers and explicit trailing account-total footers; malformed-width and data-after-footer records become invalid rows that block publication. Five tests cover success, alternate profile headers, header/footer failures, non-omission and size/encoding rejection. It is not yet a CLI file-input path and is not Fidelity-validated. Next: connect a synthetic CSV fixture to a safe CLI command with exact-source hashing and redacted output.

September 20 evening: added an immutable, validated synthetic mapping profile that versions the source header map, row classifications, currency and exact-decimal rounding policy. Alternate invented headers work only through an explicit valid profile; duplicate headers, unknown versions/currencies, unsupported classifications and implicit rounding fail before row mapping. This is profile infrastructure, not a Fidelity profile. Next: add a synthetic delimited-file parser boundary with header/footer accounting and safe diagnostics while awaiting the private representative export.

September 20 afternoon: added `--broker-demo`, a no-file/no-network command that runs two invented rows through the synthetic mapping and reconciliation path. The subprocess test verifies reconciliation, lossless row accounting, explicit non-Fidelity readiness and suppression of the position symbol in output. Next: define a versioned mapping-profile contract for headers, row classifications and rounding decisions without claiming a Fidelity profile before the private representative export is reviewed.

September 20 morning: M1 began with a strict synthetic broker-shaped mapping harness. It converts invented account keys and equity/cash/core-cash rows into the normalized import contract, preserves unsupported or malformed rows as explicit outcomes and reuses fail-closed reconciliation. Eight tests cover success, unsupported options, malformed/footer rows, account coverage, duplicate cash, total mismatch, stale input and strict schemas. This does not establish Fidelity compatibility. Next: expose a safe synthetic command-line/demo path while awaiting the representative privately redacted export.

September 19 evening: Research preview now displays a fixed metric trace produced by the combined eligibility gate, including value, unit/currency, reporting dates, availability time, transformation version and a missing-identity block code. M0 engineering scope is delivered, but milestone acceptance remains pending founder review and browser/device QA. M1 is active next; implement a synthetic broker-format mapping harness while awaiting the private representative export.

September 16 afternoon: combined metric eligibility gate now withholds values until point-in-time/identity/rights, payload binding and numeric availability all pass. Next: expose a synthetic metric trace in the Research preview so founder can inspect dates, units and blocked reasons; browser/device QA remains outstanding. Root README-only main-page update awaits explicit authorization requested in chat.

September 16 morning: metric payload/hash binding and explicit reporting dates implemented with seven synthetic tests, including revision selection and independent canonical-byte expectations. Next: explicit metric-bearing readiness gate combining payload binding with existing point-in-time/identity/rights controls, without changing the meaning of the existing metadata-only gate. Browser/device QA remains pending.

September 15 evening: added immutable metric definitions, finite Decimal/unavailable values and same-definition compatibility checks (unit, currency, period, formula and versions). Eight new tests pass. This is not a sourced metric catalog or readiness integration. Next: bind metric values/definitions to point-in-time observation evidence and reporting-period dates; retain browser/device QA as pending.

September 15 afternoon: connected the five-area overview, interactive put form and read-only phase checklist through exact allowlisted local routes. HTTP tests verify round-trip links and rejection of arbitrary file/query paths. UX-01 remains pending browser/device QA and founder feedback. Next bounded backend priority: metric definitions (units, currency, period, null policy and transformation compatibility); do not count blocked visual QA as completed.

September 14 afternoon: UX-01 first slice implemented as an offline five-area HTML preview with expandable arithmetic, failure-state and option-risk examples. Displayed values are now bound to a fixed risk-kernel model by regression tests. Browser/device verification and founder validation remain pending; local and cloud browser routes were unavailable in the current runtime. Next: browser QA in a capable environment and founder feedback, followed by kernel-backed editable scenarios. R13 remains planned, not delivered by the preview.

September 14: the normalized-source/replay path, effective-dated identity, use-specific rights, point-in-time observation selection and combined research-input gate are implemented with synthetic tests. R04, R06 and R15 remain partial: Fidelity mapping, production persistence, populated evidence, actual license review, metric registry and experiment registry are pending.

Founder steering, September 14: prioritize a clickable synthetic screen prototype by September 19 and product-oriented briefings showing what can be tried. See product/README.md for screen concepts and the preview timeline. The metric-definition registry covering units, currency, period, null policy and transformation compatibility follows as a backend dependency. Fidelity mapping remains dependent on a redacted representative sample. Continue useful work without repeatedly asking for the same approval.

September 15 morning: added the first editable kernel-backed UX slice—a localhost-only, non-persistent cash-secured-put expiration form with fail-closed validation and HTTP security/integration tests. UX-01 remains partial until browser/device QA and founder workflow validation. Next: integrate the local Options Lab into the five-area navigation and complete browser/accessibility checks; metric registry remains the next financial-data foundation.
