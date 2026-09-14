# Atlas — portfolio research and risk platform

Working name; trademark and domain availability are unverified. Target: a private, read-only research prototype by **December 12, 2026**. Current release: **0.1 foundation**, a local calculation kernel with synthetic demo. Not a customer-ready service.

Atlas will connect portfolio exposure, company fundamentals, economic conditions, systematic signals and option scenarios into an explainable weekly research process. Benchmark outperformance is a research hypothesis, never a product guarantee.

## What you can try and when — updated September 14, 2026

The default repository page still shows the legacy README on `main`. Active Atlas work is in [draft PR #1](https://github.com/lvlunario/quant_trading_tool/pull/1); use this branch's product README for current progress. The merge remains a founder acceptance decision.

Today: two local Python command-line demos are available, using synthetic data. There is no browser dashboard, hosted login, Fidelity connection or working stock-analysis feed yet. The latest verified implementation has 77 passing tests; test count measures verification coverage, not product completeness.

| Target | Founder experience | Dependency / state |
|---|---|---|
| Now | Run portfolio arithmetic and research-input checks locally using the commands below | Implemented; synthetic data only |
| September 19 | Review an early clickable screen prototype: dashboard, holdings, stock research and option scenarios | New near-term UX target; synthetic content, not yet implemented; M0 acceptance remains separate |
| October 3 | Try a reconciled portfolio-import workflow | Requires representative redacted Fidelity export; browser delivery is not implied by this milestone |
| October 17 | Review a sourced stock-research workbench and weekly report | Requires verified identities and permitted data; first version may be local/report-based |
| October 31 | Try documented strategy experiments and option-risk scenarios | Data, benchmark and cost validation required |
| November 14 | Use the first integrated private browser application | Authentication, approved private storage and data access required |
| November 28 | Test the release candidate and paper-portfolio workflow | Feature scope closes for stabilization |
| December 12 | Accept the usable private read-only/paper prototype | Founder UAT and release gates; not a commercial or real-money launch |

Dates are delivery targets, not claims that these features already exist. Protect November 28–December 12 for stabilization.

## How the product will look

Planned navigation: **Overview · Portfolio · Research · Options Lab · Weekly Review**.

- **Overview:** portfolio value, cash, concentration, changes since last review and a prominent data freshness/completeness indicator.
- **Portfolio:** account aliases and positions, allocation views, import reconciliation and rows requiring attention.
- **Research:** watchlist, business/fundamental metrics, valuation, catalysts, macro exposure, cited evidence and counterarguments. Unresolved instruments remain visible as blocked.
- **Options Lab:** covered-call and cash-secured-put scenarios showing premium, collateral, breakeven, assignment exposure, capped upside and downside. Current chains and reconciled collateral are prerequisites for actionable comparisons.
- **Weekly Review:** what changed, research findings, missing evidence and a decision journal. Recommendations and performance claims require validated evidence.

The first screen prototype will use clearly labeled synthetic values and let the founder review navigation and workflow before account/data integration. It will not display invented live quotes or simulated results as measured performance.

Product briefings will lead with what the founder can see or try, the next visible deliverable and its date, then tests, risks and decisions. The next implementation priority is the synthetic screen prototype; metric-registry work remains a backend dependency.

## Run the foundation

Use Python 3.11 or later. This kernel uses only the standard library; it does not need the experimental root requirements.

```bash
cd product
python -m unittest discover -s tests -v
python -m atlas --demo
python -m atlas --research-demo
python -m atlas --snapshot /absolute/private/path/snapshot.json
python -m atlas --reconcile /absolute/private/path/normalized-import.json
python -m atlas --reconcile /absolute/private/path/normalized-import.json \
  --ledger /absolute/private/path/import-audit.sqlite3
```

The demo uses invented `DEMO` shares and hypothetical prices. Output includes snapshot concentration and a put downside scenario. No market-data calls, account linking, order placement, or model recommendations exist yet. Keep any real input/output outside the repository, including GitHub issues and CI logs.

## Program manual

The `atlas.ingestion` interface and `--reconcile` command validate versioned normalized rows, produce per-row outcomes, and block publication when account totals or positions disagree. The optional private SQLite ledger records only an opaque source ID, exact-source SHA-256, outcome and first-seen time; it suppresses publication on exact replay. See [import contract](docs/IMPORT_CONTRACT.md). The implemented adapter accepts Atlas-normalized JSON only—it is not a Fidelity CSV parser.

The `atlas.reference` contracts resolve effective-dated security identities without treating ticker labels as stable IDs and block dataset use unless current evidence explicitly permits the requested purpose. See [security master and data-rights contract](docs/SECURITY_MASTER.md). No real watchlist records or provider permissions are populated yet.

The `atlas.provenance` contract records when a source revision became available and selects only evidence available at a historical decision time. See [point-in-time provenance](docs/PROVENANCE.md). This is synthetic contract infrastructure, not a populated research dataset or backtest.

`--research-demo` runs the combined point-in-time, effective-identity and current-data-rights gate using invented metadata. A `ready` result means those three contract gates passed only; it is not a statement about source accuracy, investment quality or commercial readiness.

- [Founder phase approval checklist: what to verify, try and sign off](docs/PROGRAM.md#founder-phase-acceptance-checklist)
- [Program, roles, approvals and deadlines](docs/PROGRAM.md)
- [Requirements and metric inventory](docs/REQUIREMENTS.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Research validation and quality](docs/QUALITY.md)
- [Security and real-money release gates](docs/SECURITY.md)
- [Commercial and financing readiness](docs/COMMERCIAL.md)
- [Backlog and decisions](docs/BACKLOG.md)
- [Daily evidence logs](docs/daily/)
- [Iteration review packets](docs/reviews/)

The root `src/` quantum experiment is legacy research and is not imported by Atlas. Its historical validation approach is not accepted performance evidence.
