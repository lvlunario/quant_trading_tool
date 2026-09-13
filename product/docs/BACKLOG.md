# Backlog and decision register

Priority order is dependency-driven. GitHub issue links will accompany the launch PR.

| ID | Work item | Priority | Due | Owner role | Exit |
|---|---|---|---|---|---|
| SEC-01 | Review inherited tracked .env privately; rotate if needed | P0 | Sep 13 | Founder/security | Review recorded without exposing values |
| ENG-01 | Foundation CI and CLI error-path tests | P0 | Sep 19 | Engineering/QA | CI on exact commit; tests and demo pass |
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

September 13: an explicit normalized-source adapter boundary, exact-byte SHA-256 provenance and optional atomic hash-only SQLite replay ledger are implemented with synthetic tests; R04 remains partial. The ledger blocks source identity conflicts and suppresses exact-replay publication, but is local prototype infrastructure rather than production audit storage.

Next, specify security-master identities and data-rights evidence while Fidelity mapping remains dependent on a redacted representative sample. When the sample is available, map it through the adapter boundary and extend reconciliation for observed cash/core, unsettled and option semantics. Continue useful work without repeatedly asking for the same approval.
