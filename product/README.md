# Atlas — portfolio research and risk platform

Working name; trademark and domain availability are unverified. Target: a private, read-only research prototype by **December 12, 2026**. Current release: **0.1 foundation**, a local calculation kernel with synthetic demo. Not a customer-ready service.

Atlas will connect portfolio exposure, company fundamentals, economic conditions, systematic signals and option scenarios into an explainable weekly research process. Benchmark outperformance is a research hypothesis, never a product guarantee.

Project decisions are now delegated to engineering: the private read-only/paper scope and synthetic fallback are adopted, and M0’s engineering baseline is conditionally accepted for continued development. Browser/device QA and final release acceptance remain open. See [decision record](docs/PROGRAM.md#delegated-project-decisions--september-22-2026).

## What you can try and when — updated October 6, 2026

The default repository page still shows the legacy README on `main`. Active Atlas work is in [draft PR #1](https://github.com/lvlunario/quant_trading_tool/pull/1); use this branch's product README for current progress. The merge remains a founder acceptance decision.

Today: fourteen local Python command-line reports/demos, an offline HTML workflow preview, a localhost-only interactive Options Lab, a fixed localhost Import Demo and a read-only Research workbench are available. Research shows a contract-backed synthetic metric, its exact document/provider/dataset provenance, the explicit blocked real-provider qualification state and an invented macro series with original, revised and not-yet-available states. It also shows the public source-rights queue: all eight resolved securities are blocked for missing review evidence, with retrieval disabled and release unauthorized. The M2 Research workbench composes the full nine-name universe and distinguishes unresolved identity, missing source candidate and missing rights evidence through four fixed, allowlisted routes without exposing source/review evidence. Its worksheet-readiness panel reports safe aggregate progress—eight reviews pending and zero of 64 required checks complete—while keeping private source and review details out of the page. M1 now has a runnable broker-mapping demonstration, a versioned synthetic profile and a bounded synthetic CSV command that requires exact headers, derives account totals from explicit footer rows and retains malformed records as failures. An optional private hash-only ledger prevents an identical file from publishing rows twice. The October 3 handoff accepts only this synthetic engineering scope for progression and defers Fidelity validation. M2 now has exact source-document-to-metric binding, a separate macro release/vintage contract, a bounded permission-gated source intake boundary, a fixed end-to-end synthetic source workflow, explicit extraction-quality evidence, a zero-tolerance synthetic extractor conformance suite and a fail-closed private-provider qualification protocol. A dated [weekly public-evidence watchlist report](docs/research/2026-10-03-weekly-watchlist.html), strict current-identity registry and eight-item issuer-source candidate catalog start the sourced-workbench workflow. The catalog links every resolved identity to a dated official issuer-release address; CRBS remains unresolved and uncatalogued. A deterministic blank worksheet now binds all eight source candidates to the exact reviewed-evidence fields and eight-step checklist while directing completed evidence to private storage. A separate review manifest records that terms evidence has not been reviewed and keeps network retrieval disabled. A reviewed-evidence schema distinguishes permitted, prohibited, counsel-required, expired, ambiguous and missing decisions. No actual reviewed record is checked in, so rights, extraction and all metric values remain unavailable. These artifacts rank research priority and verify public metadata; they do not rank securities or approve source use. The importer is not a Fidelity adapter. There is no hosted login, Fidelity connection or licensed stock-analysis feed yet. The latest local suite has 256 passing tests; test count measures verification coverage, not product completeness.

Portfolio now shows four contract-backed synthetic import receipts: eligible, blocked, duplicate and replay check required. Each displays only controlled state and row counts—never account aliases, totals, holdings or file paths. The offline page still does not accept a file or run an import. The localhost Import Demo runs only the checked-in invented CSV through the same parser, reconciliation and receipt pipeline used by the command-line workflow; it accepts no upload or caller-selected path. The adjacent M1 Conformance view shows four synthetic checks verified, four Fidelity-specific checks blocked on external evidence and private persistence not implemented. It now derives the October 3 engineering recommendation: accept only the synthetic evidence, defer Fidelity validation and continue the fallback; it cannot record founder approval or release authorization.

### Try the offline screen preview

On this branch, download [preview/index.html](preview/index.html) using GitHub's **Download raw file** control, then open the downloaded HTML in a desktop browser. Or open `product/preview/index.html` from your local checkout. No server, install or account login is needed. GitHub's file view displays source, not the running preview. The phase-checklist link requires the full checkout or reading the linked manual here on GitHub.

Click the five navigation links, inspect the four redacted import receipt states, expand the portfolio arithmetic and incomplete-import warning, inspect Research's exact synthetic source, blocked source-rights queue, blocked provider qualification and macro-vintage states, then compare the three Options Lab outcomes. See [preview review instructions](preview/README.md). The page contains fixed, non-editable examples. The checked-in values are regression-tested against the financial, source-binding, rights-evidence, provider-qualification and macro-vintage contracts, but the HTML does not call Python at runtime. It saves nothing and makes no network requests. Browser rendering verification is recorded separately in the daily log; structural and value-contract tests do not prove usability.

When served locally, choose **Open Research workbench** or open
`http://127.0.0.1:8765/research-work-items`. Its All, Identity, Source candidate
and Rights review views are exact allowlisted routes; query-string filters are
rejected. The workbench shows aggregate blank-worksheet progress but excludes
source addresses and evidence-field names. It is read-only and does not retrieve
or persist evidence.

For an editable synthetic put scenario, start the local Options Lab from a terminal:

```bash
cd product
python -m atlas --preview-server
```

Open the displayed `http://127.0.0.1:8765/overview` address. In Portfolio, select **Run fixed synthetic import demo** and verify the replay-check-required receipt, then select **View M1 conformance** to inspect the evidence boundary. Then select **Open interactive Options Lab** in the Options section. Change strike, premium, expiration price, total fees or available cash, calculate, then use **Return to five-area overview**. Weekly Review links to the read-only founder checklist. Press **Ctrl+C** in the terminal to stop it. The server binds only to the local computer, stores nothing and calculates one standard cash-secured-put expiration scenario through `atlas.risk`. Use invented inputs only. This is not the authenticated November application and contains no quote, broker, account or order connection.

| Target | Founder experience | Dependency / state |
|---|---|---|
| Now | Run portfolio arithmetic, fixed CSV reconciliation, receipt and research-input checks locally | Implemented; synthetic data only; no file upload or account connection |
| September 19 | Review an early clickable screen prototype: dashboard, holdings, stock research and option scenarios | Offline navigation plus local editable kernel-backed put scenario implemented; M0 engineering baseline conditionally accepted for progression; full browser/device QA and founder workflow feedback pending |
| October 3 | Try a reconciled portfolio-import workflow | Synthetic engineering scope accepted for progression; Fidelity validation deferred pending a representative authorized export and provisioned private boundary |
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

Latest asynchronous review: [October 5 M2 concept and iteration packet](docs/reviews/2026-10-05-M2.md). It presents evidence and recommended defaults; it is not a completed meeting or founder approval.

## Run the foundation

Use Python 3.11 or later. This kernel uses only the standard library; it does not need the experimental root requirements.

```bash
cd product
python -m unittest discover -s tests -v
python -m atlas --demo
python -m atlas --research-demo
python -m atlas --source-demo
python -m atlas --extractor-conformance-demo
python -m atlas --provider-qualification-demo
python -m atlas --m1-handoff
python -m atlas --watchlist-registry-demo
python -m atlas --source-catalog-demo
python -m atlas --source-rights-demo
python -m atlas --rights-review-worksheet-demo
python -m atlas --rights-evidence-demo
python -m atlas --research-work-items-demo
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

The `atlas.source_evidence` contract binds a selected metric observation to one exact instrument-level source record before releasing its value. See [research source-document contract](docs/RESEARCH_SOURCE_CONTRACT.md). It verifies internal consistency and timing, not publisher authenticity, accuracy or permission.

The `atlas.source_intake` boundary admits already-retrieved bytes only after
strict size/encoding checks and explicit current permission for the intended
use, then returns exact-byte metadata without retaining content. See [permitted
source intake contract](docs/SOURCE_INTAKE.md). It does not fetch, persist,
authenticate or extract documents.

`--source-demo` runs the checked-in invented JSON source through permission
checking, exact-byte intake, typed extraction, point-in-time observation,
security identity and sourced-metric readiness. Its redacted output contains a
digest and released metric fields, not the URI or raw document. This is a fixed
contract demonstration—not a provider adapter, general upload or accuracy
claim.

The source demo also records whether extraction was deterministic, manual or
AI-assisted and binds that claim to the exact source and metric payload hashes.
Manual or AI-assisted values remain blocked without verified review evidence.
See [extraction-quality contract](docs/EXTRACTION_QUALITY.md).

`--extractor-conformance-demo` runs six checked-in invented positive/negative
cases and requires full category coverage with zero false accepts, false rejects
or other expectation mismatches. The all-pass result is synthetic contract
evidence—not real-provider compatibility or a measured accuracy rate. See
[extractor conformance contract](docs/EXTRACTOR_CONFORMANCE.md).

`--provider-qualification-demo` reports the adopted real-provider evidence
protocol and intentionally returns blocked while the private boundary,
authorized representative corpus, independent labels and measured quality are
absent. Its output omits evidence identifiers and can never authorize release.
See [private provider qualification](docs/PROVIDER_QUALIFICATION.md).

`--m1-handoff` returns the October 3 machine-readable disposition. It advances
only the verified synthetic engineering scope to M2, keeps Fidelity validation
deferred and cannot record founder approval or authorize release. See the
[M1 disposition](docs/reviews/2026-10-03-M1-disposition.md).

`--watchlist-registry-demo` validates the October 3 public identity snapshot
for eight resolved Nasdaq securities and the explicitly unresolved CRBS entry.
It contains no prices, holdings, provider-license claim or investment outcome.
See the [security-master contract](docs/SECURITY_MASTER.md).

`--source-catalog-demo` validates eight dated official issuer-release addresses
for every resolved watchlist identity against the stable identity registry.
It deliberately reports rights as not evaluated, extraction as not attempted
and every metric as unavailable. It fetches no document and makes no accuracy,
license or investment claim. See the [source-document contract](docs/RESEARCH_SOURCE_CONTRACT.md).

`--source-rights-demo` projects the document-level review queue and a bounded
future retrieval policy. It correctly exits blocked: no terms evidence is
recorded, network fetching and redirects are disabled, bytes are not retained
and no permission conclusion is made. See the [source-rights review contract](docs/SOURCE_RIGHTS_REVIEW.md).

`--rights-review-worksheet-demo` emits the deterministic blank worksheet for
all eight candidates: exact public source bindings, evidence-field names,
allowed conclusions/actions and the pending eight-step checklist. It records no
evidence value or reviewer and directs completed material to private storage.

`--rights-evidence-demo` assesses the reviewed-evidence register. The checked-in
register is deliberately empty, so all eight candidates report missing evidence
and the command exits blocked. Even complete rights evidence cannot enable
technical retrieval or authorize release by itself.

`--research-work-items-demo` composes the current identity registry, eight-name
source catalog and empty reviewed-evidence register into nine public-safe work
items. It distinguishes unresolved identity, missing source candidates and
missing rights evidence while withholding extraction, metrics and release. It
contains no source/review identifiers, hashes, prices or recommendations.

The `atlas.macro_vintages` contract keeps original and revised economic releases separate and selects only the vintage available at a historical decision time. See [macro release and vintage contract](docs/MACRO_VINTAGES.md). No real macro provider or economic forecast is included.

`--research-demo` runs the combined point-in-time, effective-identity and current-data-rights gate using invented metadata. A `ready` result means those three contract gates passed only; it is not a statement about source accuracy, investment quality or commercial readiness.

- [Founder phase approval checklist: what to verify, try and sign off](docs/PROGRAM.md#founder-phase-acceptance-checklist)
- [Program, roles, approvals and deadlines](docs/PROGRAM.md)
- [Requirements and metric inventory](docs/REQUIREMENTS.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Research validation and quality](docs/QUALITY.md)
- [Research extraction-quality contract](docs/EXTRACTION_QUALITY.md)
- [Synthetic extractor conformance contract](docs/EXTRACTOR_CONFORMANCE.md)
- [Private provider-extractor qualification protocol](docs/PROVIDER_QUALIFICATION.md)
- [Security and real-money release gates](docs/SECURITY.md)
- [Commercial and financing readiness](docs/COMMERCIAL.md)
- [Backlog and decisions](docs/BACKLOG.md)
- [Daily evidence logs](docs/daily/)
- [Iteration review packets](docs/reviews/)

The root `src/` quantum experiment is legacy research and is not imported by Atlas. Its historical validation approach is not accepted performance evidence.
