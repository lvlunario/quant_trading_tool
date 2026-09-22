# Atlas — portfolio research and risk platform

Working name; trademark and domain availability are unverified. Target: a private, read-only research prototype by **December 12, 2026**. Current release: **0.1 foundation**, a local calculation kernel with synthetic demo. Not a customer-ready service.

Atlas will connect portfolio exposure, company fundamentals, economic conditions, systematic signals and option scenarios into an explainable weekly research process. Benchmark outperformance is a research hypothesis, never a product guarantee.

Project decisions are now delegated to engineering: the private read-only/paper scope and synthetic fallback are adopted, and M0’s engineering baseline is conditionally accepted for continued development. Browser/device QA and final release acceptance remain open. See [decision record](docs/PROGRAM.md#delegated-project-decisions--september-22-2026).

## What you can try and when — updated September 22, 2026

The default repository page still shows the legacy README on `main`. Active Atlas work is in [draft PR #1](https://github.com/lvlunario/quant_trading_tool/pull/1); use this branch's product README for current progress. The merge remains a founder acceptance decision.

Today: four local Python command-line demos, an offline HTML workflow preview and a localhost-only interactive Options Lab are available using synthetic data. Research shows a synthetic, gate-backed metric trace with its units, reporting dates, availability time and blocked-state example. M1 now has a runnable broker-mapping demonstration, a versioned synthetic profile and a bounded synthetic CSV command that requires exact headers, derives account totals from explicit footer rows and retains malformed records as failures. An optional private hash-only ledger prevents an identical file from publishing rows twice. It is not a Fidelity adapter. There is no integrated browser dashboard, hosted login, Fidelity connection or working stock-analysis feed yet. The latest local suite has 134 passing tests; test count measures verification coverage, not product completeness.

### Try the offline screen preview

On this branch, download [preview/index.html](preview/index.html) using GitHub's **Download raw file** control, then open the downloaded HTML in a desktop browser. Or open `product/preview/index.html` from your local checkout. No server, install or account login is needed. GitHub's file view displays source, not the running preview. The phase-checklist link requires the full checkout or reading the linked manual here on GitHub.

Click the five navigation links, expand the portfolio arithmetic and incomplete-import warning, then compare the three Options Lab outcomes. See [preview review instructions](preview/README.md). The page contains fixed, non-editable examples. The checked-in values are regression-tested against `atlas.risk`, but the HTML does not call Python at runtime. It saves nothing and makes no network requests. Browser rendering verification is recorded separately in the daily log; structural and value-contract tests do not prove usability.

For an editable synthetic put scenario, start the local Options Lab from a terminal:

```bash
cd product
python -m atlas --preview-server
```

Open the displayed `http://127.0.0.1:8765/overview` address. Navigate the five product areas, then select **Open interactive Options Lab** in the Options section. Change strike, premium, expiration price, total fees or available cash, calculate, then use **Return to five-area overview**. Weekly Review links to the read-only founder checklist. Press **Ctrl+C** in the terminal to stop it. The server binds only to the local computer, stores nothing and calculates one standard cash-secured-put expiration scenario through `atlas.risk`. Use invented inputs only. This is not the authenticated November application and contains no quote, broker, account or order connection.

| Target | Founder experience | Dependency / state |
|---|---|---|
| Now | Run portfolio arithmetic and research-input checks locally using the commands below | Implemented; synthetic data only |
| September 19 | Review an early clickable screen prototype: dashboard, holdings, stock research and option scenarios | Offline navigation plus local editable kernel-backed put scenario implemented; full browser/device QA and founder feedback pending; M0 acceptance remains separate |
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

Product briefings lead with what the founder can try, its next visible deliverable/date, tests, risks and decisions. The connected local preview is available; browser/device QA and founder feedback remain pending. The [metric-semantics contract](docs/METRICS.md) is now implemented as a backend dependency; sourced values and research integration remain pending.

Latest asynchronous review: [September 21 M1 concept and iteration packet](docs/reviews/2026-09-21-M1.md). It presents evidence and recommended decisions; it is not a completed meeting or founder approval.

## Run the foundation

Use Python 3.11 or later. This kernel uses only the standard library; it does not need the experimental root requirements.

```bash
cd product
python -m unittest discover -s tests -v
python -m atlas --demo
python -m atlas --research-demo
python -m atlas --broker-demo
python -m atlas --synthetic-csv-demo fixtures/synthetic-broker.csv
python -m atlas --synthetic-csv-demo fixtures/synthetic-broker.csv \
  --ledger /absolute/private/path/import-audit.sqlite3
python -m atlas --snapshot /absolute/private/path/snapshot.json
python -m atlas --reconcile /absolute/private/path/normalized-import.json
python -m atlas --reconcile /absolute/private/path/normalized-import.json \
  --ledger /absolute/private/path/import-audit.sqlite3
```

The demos use invented `DEMO` shares and hypothetical prices. `--broker-demo` runs two invented rows through the mapping and reconciliation path. `--synthetic-csv-demo` reads only the checked-in invented fixture, hashes its exact bytes, applies the bounded parser and prints safe counts/outcomes without position fields. Its source time is generated when the demo runs, not read from a broker statement. With `--ledger`, the first attempt is recorded and an identical retry returns zero publishable rows. Both remain explicitly not Fidelity-validated. The other demo output includes snapshot concentration, a put downside scenario and research-contract readiness. No market-data calls, account linking, order placement, or model recommendations exist yet. Keep any real input/output outside the repository, including GitHub issues and CI logs.

## Program manual

The `atlas.ingestion` interface and `--reconcile` command validate versioned normalized rows, produce per-row outcomes, and block publication when account totals or positions disagree. The optional private SQLite ledger records only an opaque source ID, exact-source SHA-256, outcome and first-seen time; it suppresses publication on exact replay. See [import contract](docs/IMPORT_CONTRACT.md). The general implemented adapter accepts Atlas-normalized JSON only. A separate synthetic broker-shaped mapping harness uses a validated, immutable profile for headers, row semantics, currency and rounding policy. Its demo CSV boundary is size/encoding limited, requires exact profile headers, accounts for footer and malformed records, and emits an exact-byte hash with redacted results. It is not a Fidelity CSV parser and should be used only with invented data.

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
