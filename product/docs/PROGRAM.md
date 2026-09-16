# Program baseline — September 12, 2026

## Mandate and acceptance

The founder is Program Manager and Director, accountable for scope, spending, customer promises and release acceptance. The AI implementation team prepares designs, code, tests, review packets and recommended decisions. AI workstreams are roles, not employed people, licensed professionals or independent certifications. No hires or vendors have been commissioned.

First customer: the founder, using permissioned account data. The product begins with USD listed-equity research and covered-call/cash-secured-put scenario analysis. Its differentiation hypothesis is an auditable link from portfolio exposure to investment thesis, research evidence, scenario losses and a weekly decision record. Validate this with users rather than assuming demand.

Three-month goal: a usable private prototype on December 12, 2026. This is a planning target subject to data access, review capacity and funding, not a guaranteed commercial or regulated launch. Deliver useful fallback scope if licensed options history or account linking is delayed.

## Stakeholders and responsibility

| Workstream | Responsible role | Review/decision | Required evidence |
|---|---|---|---|
| Product/customer discovery | AI product lead + founder | Founder | User stories, workflow demonstration, acceptance notes |
| Architecture/integration | AI engineering lead | Founder accepts material tradeoffs | ADRs, interface contracts, migration plans |
| Data and quant | AI research/data lead | External quant reviewer before commercial performance claims | Provenance, experiments, out-of-sample results |
| QA | AI test role; independent human QA before customer launch | Founder release decision | Requirements traceability, reproducible tests, defects |
| Security/operations | AI security design role | Qualified external security reviewer before real customer hosting | Threat model, penetration test, restoration exercise |
| Legal/compliance | External counsel, not yet engaged | Founder + qualified counsel | Written business/jurisdiction assessment and launch conditions |
| Investor readiness | AI financing support | Founder approves outreach/materials | Validated narrative, use of funds, data-room checklist |

AI checks do not replace independent human security, legal or investment review. Record who actually reviewed each artifact and distinguish proposed, reviewed, approved and released states.

## Milestones

| Gate | Deadline (Asia/Manila) | Deliverable | Exit evidence |
|---|---|---|---|
| M0 Foundation | Sep 19 | Charter, risk kernel, backlog, CI, decision packet | Tests pass; founder responds to scope proposal |
| M1 Portfolio truth | Oct 3 | Redacted Fidelity import, reconciliation, profile intake | Accepted rows reconcile; unknown rows block complete status; fixtures cover cash/options/duplicates |
| M2 Research workbench | Oct 17 | Security master, filings, fundamentals, macro and weekly report | Every material fact dated and sourced; stale/missing states visible |
| M3 Strategy laboratory | Oct 31 | Baselines, walk-forward equity tests, option scenarios | Leakage checks, costs, benchmarks, reproducibility and sensitivity review |
| M4 Private application | Nov 14 | Authenticated single-customer dashboard, jobs, alerts | End-to-end import-to-report test, access tests and recovery demonstration |
| M5 Release candidate | Nov 28 | Paper portfolio, support runbook, usability and security review | No unresolved critical defects; known limitations reviewed; data rights verified |
| M6 Prototype acceptance | Dec 12 | Stable private prototype and investor demonstration | Two-week stabilization, founder UAT, release notes and rollback test |

Critical path: data contract → reconciliation → verified market/fundamental data → research evaluation → private UI → acceptance. Begin security design and vendor licensing in parallel. A three-month paper record is operational evidence, not proof of durable alpha.

If M1 slips: use manual redacted exports. If historical options access slips: deliver payoff/stress scenarios and forward paper observation, not invented option backtests. If independent security review or legal classification is unresolved: restrict to local synthetic demonstrations. Preserve stabilization time by reducing features, and present recovery choices before moving dates.

## Delivery cadence

Request three flexible sessions each day: morning, afternoon and evening in Asia/Manila. Scheduler configuration and successful creation are recorded separately; a plan alone is not an active task. Timing may vary within supported windows; this is not guaranteed random timing or a continuously running agent. Each run should complete one bounded useful change when access and runtime allow. No empty commits or invented activity.

Each report: phase and next deadline; shipped change; test evidence; commit/PR links; forecast; risk/blocker; next action; decisions requested. Evening sessions summarize the day. Monday morning replaces the regular briefing with a concept/iteration review packet: demo, research/engineering concept, planned vs actual, risks, up to three decisions. A packet is not a meeting or approval.

Saturday morning adds weekly equity/macro research for the named universe, using fresh available evidence. Portfolio-specific conclusions require actual current holdings. Only synthetic research artifacts belong in this public repository; deliver personal results privately. After December 12, review acceptance and maintenance needs before expanding development scope.

## Change and approval control

Routine reversible implementation and tests are authorized. Use feature branches, conventional commits and reviewable PRs. Founder acceptance is required for milestone sign-off and merges. Paid subscriptions, hires, production deployment, customer data collection, public commercial claims, investor outreach and real-money execution require concrete review and explicit authorization. Never infer a financial trade approval from approval to build software.

Each change links requirement → issue → code → test evidence → PR → release. Record actual dates and AI assistance. Keep decision records with alternatives, rationale, consequences, owner and status. Report slips honestly; don't count document creation as completed implementation.

## Founder phase acceptance checklist

Added September 14, 2026 at founder request. All boxes below are unchecked acceptance criteria, not evidence of delivered features or approvals. Dates are targets. The September 19 clickable synthetic preview is a UX review alongside M0, not proof of an integrated application.

**Verification:** does the implementation match its written requirement? Engineering supplies reproducible checks and expected results; the founder reviews the evidence.
**Validation:** does the demonstrated workflow solve the founder's actual problem? The founder tries representative tasks and judges usefulness and clarity. Passing tests alone cannot establish this.

### How to conduct each review

1. Open the phase packet: exact commit/build and demo instructions, planned versus delivered scope, requirement-to-test evidence, actual CI results, known defects, dependencies and the requested decision. If it is missing, mark the gate pending.
2. Follow the phase actions below. Record expected versus observed behavior and Pass / Fail / Blocked for each item. For synthetic demos use supplied fixtures; keep personal screenshots, statements, exports and results private.
3. Check a normal task and a failure task. An unavailable feature or missing dataset is Blocked, not Pass. Ask for a demonstration if setup requires developer assistance; the team supplies it.
4. Choose Approved, Changes required, or Deferred. Conditional acceptance must name the limited accepted scope, residual defects, owner role and due date; it cannot waive privacy/security or financial correctness blockers.
5. Record only the founder's actual response with date, phase, exact build and evidence references. Later material changes need a new review. Preparing this checklist is not approval.

No milestone is automatically approved by its date, test count, silence or next-phase work. Routine reversible development can continue while acceptance is pending. Merge, spending, hosting/deployment, real data collection and commercial or trading permissions are separate explicit decisions.

### M0 — Foundation and screen concept — September 19

Approving: the product boundary, delivery plan, foundational behavior and proposed user workflow.
- [ ] Read the mandate and milestones; confirm December scope is private read-only/paper and identify exclusions or changes.
- [ ] Run or watch both README synthetic demos; compare displayed value/concentration and option payoff with the team's independent worked calculation. Request an invalid-input demo and verify it stops with a clear explanation.
- [ ] Inspect exact-build CI and requirement mapping; verify reported checks were actually run and any gaps are listed.
- [ ] In the planned clickable preview, navigate Overview → Portfolio → Research → Options Lab → Weekly Review. Locate cash, concentration, data freshness and a sample holding without coaching. Verify synthetic labels stay visible.
- [ ] Explain what action you would take after each screen; identify confusing labels or missing information. This validates the concept, not Fidelity connectivity.
Evidence: charter, backlog, architecture, calculation examples, CI links, preview instructions and known limits.
Hold acceptance if: arithmetic contradicts the example, synthetic data looks live, promised screens are absent, or scope remains disputed.
Approval effect: accepts the named M0 deliverables/design baseline only; a missing UX preview must remain separately pending.

### M1 — Portfolio truth — October 3

Approving: the supported import scope and reconciled portfolio representation.
- [ ] Using a representative redacted Fidelity export in approved private storage, follow import instructions. Privately compare every included account's holdings, cash/core position and total to the export at the same timestamp.
- [ ] Check the team's reconciliation sheet: each source row is accepted, rejected or explicitly unsupported; any difference has a documented explanation and agreed rounding tolerance.
- [ ] Try supplied duplicate, malformed, stale and unsupported-position fixtures. Verify clear blocking states and that repeating an import does not duplicate portfolio state.
- [ ] Verify account aliases, currency, source time and completeness are visible; incomplete portfolios must not look ready for account-specific analysis.
- [ ] Complete profile intake and correct an intentional error. Confirm objectives, constraints and account representation match your intended use.
Evidence: private source-to-output comparison, supported-format list, reconciliation/negative-path tests, consent/storage controls.
Hold acceptance if: real Fidelity format is untested, totals differ without explanation, rows vanish, or privacy prerequisites are unmet. Synthetic contract acceptance may be recorded separately but cannot count as Fidelity acceptance.
Approval effect: accepts only tested import formats and supported assets, subject to the separate G1 data-use gate.

### M2 — Research workbench — October 17

Approving: the traceability and usefulness of stock/macro research.
- [ ] Choose two resolved securities. Open issuer, exchange and share-class identity; check primary evidence and dates. Confirm unresolved CRBS is blocked rather than silently substituted.
- [ ] Trace three material metrics from screen/report to evidence; check units, currency, reporting period, publication time and calculation definition.
- [ ] Review a historical-date example containing a later revision. Verify the later information is excluded from the earlier analysis.
- [ ] Try missing/stale evidence and absent data-permission fixtures; verify blocked/unavailable states remain visible.
- [ ] Read a weekly report and identify facts, hypotheses, counterarguments, catalysts and missing data. Decide whether it supports your weekly review.
Evidence: source-linked report, metric definitions, identity/provenance tests and purpose-specific data-rights evidence.
Hold acceptance if: facts cannot be traced, identities conflict, later data leaks backward, or intended-use permission is unverified.
Approval effect: accepts the evidenced research workflow; does not certify stock recommendations or outperformance.

### M3 — Strategy laboratory — October 31

Approving: reproducible experiments and understandable option-risk scenarios.
- [ ] Read the registered hypothesis, universe, dates, benchmark and holdout rules before examining results; verify the experiment history includes unsuccessful trials.
- [ ] Follow the supplied rerun instructions or observe the team rerun the exact experiment; compare outputs and documented tolerances.
- [ ] Inspect chronological splits, source availability, execution delays, costs and benchmark alignment. Check adverse-cost and market-regime results.
- [ ] In Options Lab, test zero underlying price, breakeven, assignment and upside above strike. Compare against independent payoff examples; verify collateral and share reservations cannot be counted twice.
- [ ] Test missing/stale chain or collateral inputs. Confirm actionable comparisons are blocked. If only payoff scenarios are delivered, record that limitation explicitly.
- [ ] Explain the potential loss, capped upside and assumptions of one scenario. Confirm premium is never presented as guaranteed safe income.
Evidence: experiment registry, reproducible outputs, holdout/cost/leakage tests, payoff examples and data limitations.
Hold acceptance if: results cannot be reproduced, holdout contamination exists, costs are omitted, or collateral/risk is misrepresented.
Approval effect: accepts research/scenario capability only; no live-money authority or proof of durable alpha.

### M4 — Integrated private application — November 14

Approving: the integrated single-customer experience within an explicitly authorized private environment.
- [ ] After the separate private access/deployment gate is satisfied, sign in, import a permitted test portfolio, inspect reconciliation, open research and produce the weekly report.
- [ ] Sign out and reopen the private URL. Observe documented unauthorized-access tests, including another user's access attempt where applicable; verify data is denied.
- [ ] Trigger a failed/stale data job and a retry using test inputs. Check visible status, timestamps, alerts and absence of duplicate results.
- [ ] Observe restore of disposable test data and compare recovered records. Review secret/log-redaction evidence without exposing credentials.
- [ ] Complete the full weekly workflow without developer coaching and record confusing steps or excessive manual work.
Evidence: end-to-end test/demo, access/security checks, job evidence, restore result and usability notes.
Hold acceptance if: unauthorized data access is possible, private deployment approval is absent, recovery fails, or core workflow cannot complete.
Approval effect: accepts demonstrated application behavior; hosting and real-data permissions must be separately recorded.

### M5 — Release candidate — November 28

Approving: the candidate scope to freeze for stabilization.
- [ ] Repeat import → research → option scenario → weekly review on the candidate build using agreed permitted fixtures.
- [ ] Review the open-defect list with severity and actual evidence. Verify no unresolved critical defect; treat incorrect portfolio/risk calculations and privacy failures as release blockers.
- [ ] Inspect paper-portfolio event history and retry/restart behavior; confirm no real order is submitted.
- [ ] Walk through export/deletion and a support/incident scenario using disposable test records; check expected retained backup/audit handling against policy.
- [ ] Review data rights, security-review findings, runbooks and all deferred features. Confirm the remaining scope is useful enough to freeze.
Evidence: candidate build, regression/UAT results, defects, security-review status, rights and operational runbooks.
Hold acceptance if: critical defects remain, required independent review is absent, data rights are missing or support/recovery is untested. Local synthetic fallback remains available under program policy.
Approval effect: accepts candidate scope for November 28–December 12 stabilization, not final release.

### M6 — Prototype acceptance — December 12

Approving: the documented private read-only/paper prototype and maintenance handoff.
- [ ] On the exact proposed release, repeat the agreed user tasks and compare outcomes with the acceptance baseline. Confirm you can complete them using the supplied instructions.
- [ ] Inspect two weeks of stabilization evidence, defect retests and regression results; absence of evidence is not a clean record.
- [ ] Observe rollback and restore on disposable test data; check stated recovery limitations and operating instructions.
- [ ] Review release notes, unresolved limitations, data rights, private-access controls and support/maintenance ownership. Confirm every earlier gate is accepted or explicitly recorded as reduced scope.
- [ ] Confirm demonstration materials contain only synthetic/redacted permitted content, and claims match evidence. Decide whether the delivered scope meets your intended private weekly workflow.
Evidence: release commit/build, completed UAT results, stabilization log, rollback/restore record and maintenance handoff.
Hold acceptance if: critical defects or G1 prerequisites remain unresolved. Do not relabel a synthetic/local fallback as a fully accepted private account prototype.
Approval effect: accepts only the named private prototype scope. Paying customers, investor outreach, production launch, real-money execution and a new development program need separate authorization.

### Decision record template

Copy into the review packet; retain personal evidence privately.

- Phase / exact commit or build:
- Review date (Asia/Manila):
- Delivered scope / omitted scope:
- Evidence references (private references only for personal results):
- Checklist results: item → expected → observed → Pass / Fail / Blocked:
- Founder decision: Pending / Approved / Changes required / Deferred:
- Conditions or defects: description / severity / responsible role / due date:
- Separate authorization, if explicitly given: exact PR merge, destination/deployment, data use or budget:
- Actual founder response, quoted faithfully:
- Recorded by / timestamp:

Default status is **Pending**. No founder phase acceptance is recorded by adding this checklist.
