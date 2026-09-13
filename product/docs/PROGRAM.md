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
