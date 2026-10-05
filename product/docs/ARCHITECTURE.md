# Architecture and decisions

October 5 M2 workbench increment: `atlas.research_work_items` composes the
effective-dated watchlist registry, public source catalog and reviewed-rights
decision into one versioned public-safe queue. Every work item remains blocked
until its earliest unmet dependency is resolved. Current primary blockers are
unresolved identity for CRBS, missing source candidates for five resolved names
and missing review evidence for NVDA, MU and AVGO. Even a permitted rights state
advances only to missing source evidence; it never enables retrieval, extraction,
metrics or release. The report omits source/review identifiers, URIs, hashes,
prices and recommendations.

October 4 M2 rights-review increment: `atlas.source_rights` requires one
document-level review record for every dated public source candidate. Version 1
accepts only `not_started`, contains no terms evidence or reviewer assertion and
returns a blocked result. Its future retrieval envelope is limited to 5 MiB and
HTML/PDF/JSON, with redirects, byte retention and network fetching disabled.
This is review tracking and planning, not permission or a downloader. See the
[source-rights review contract](SOURCE_RIGHTS_REVIEW.md).

The afternoon extension, `atlas.rights_evidence`, keeps completed terms reviews
in a separate immutable register. It requires exact document/use-case binding,
opaque reviewer references, terms hashes and times, validity, a controlled
conclusion/action set and an eight-item manual checklist. Latest non-conflicting
evidence may pass only the rights decision; technical retrieval remains disabled
and release authorization remains false. The public register is empty, so the
current watchlist remains blocked.

The evening Research projection reloads the checked-in identity, candidate and
rights-evidence fixtures through those same contracts. It allowlists only queue
status, counts, symbol-level decision codes, technical retrieval status and the
false release flag. Terms addresses, hashes, document/review identifiers and
reviewer references never enter the projection. The standalone HTML remains a
fixed regression target and does not perform a review or fetch at runtime.

September 30 M2 qualification increment: `atlas.provider_qualification`
separates public policy from private evidence and binds qualification to an
exact provider, dataset and extractor version. The adopted minimum gate requires
an authorized representative corpus, full declared-format coverage, two
reviewers, 30 documents, 200 checked fields, at least 99% exact matches and zero
critical or semantic errors. Missing, synthetic-only, expired or mismatched
evidence blocks. Reports exclude evidence identifiers and cannot authorize a
release. See [provider qualification protocol](PROVIDER_QUALIFICATION.md).

The fixed Research projection consumes the no-evidence qualification decision
and displays only its controlled status, counts, rates and blocking code. It
does not construct an independent UI status or expose corpus/label hashes,
reviewer identities or authorization receipts. A regression test requires the
offline HTML and localhost overview to remain equal to the backend decision.

September 30 M2 conformance increment: `atlas.extractor_conformance` evaluates
one versioned invented provider/dataset/extractor profile against a bounded
manifest of positive and negative cases. Required category coverage and
zero-tolerance false-accept, false-reject and expectation-mismatch limits fail
closed. Results contain case classifications but no source objects. This is
synthetic contract regression evidence, not provider compatibility or measured
production accuracy. See [extractor conformance contract](EXTRACTOR_CONFORMANCE.md).

September 29 M2 extraction increment: `atlas.extraction_quality` binds a
versioned extraction method and review state to the exact source document and
canonical metric payload. Deterministic parsing may be self-evidencing under a
fixed contract; manual and AI-assisted extraction require a verified review
digest. Rejected, unverified, mismatched or temporally impossible evidence
withholds the value. Research now projects this composed synthetic decision.
See [extraction-quality contract](EXTRACTION_QUALITY.md).

September 29 M2 workflow increment: `atlas.source_workflow` runs one checked-in
invented JSON source through the permission-first intake boundary, strict typed
extraction, point-in-time observation construction, effective security identity
and exact-source metric readiness. The CLI exposes only a redacted report. The
adapter accepts no path or URL and is deliberately not reusable for real source
files; provider retrieval, private persistence and extraction qualification
remain separate work.

September 29 M2 intake increment: `atlas.source_intake` accepts only
already-retrieved exact bytes, enforces a 5 MiB bound and controlled
encoding/signature checks, checks current purpose-specific data rights before
hashing, and emits `ResearchSourceRecord` metadata without retaining content.
It performs no network retrieval, persistence, publisher authentication,
malware scan or fact extraction. See [permitted source intake contract](SOURCE_INTAKE.md).

September 28 M2 macro-vintage increment: `atlas.macro_vintages` gives economic
series a dedicated identity rather than a fake security/ticker. Each reporting
period retains original and revised releases with Decimal/missing values,
availability/observation times, source hash and transform version. Historical
selection admits only the latest vintage available at the decision time, then
applies purpose-specific data rights. No real provider, series or forecast is
implemented. See [macro vintage contract](MACRO_VINTAGES.md).

September 28 M2 source-boundary increment: `atlas.source_evidence` records exact
instrument-level source bytes with stable instrument/provider/dataset IDs,
controlled kind/content type, publication/availability/retrieval times, HTTPS
URI and SHA-256 digest. `assess_sourced_metric_input` releases a metric only
after the existing point-in-time, identity, rights, payload and numeric gates
also bind to that exact source. This is internal consistency evidence, not
publisher authentication, source accuracy, permission, persistence or a
populated research feed. See [research source contract](RESEARCH_SOURCE_CONTRACT.md).

September 27 evening: `recommend_m1_disposition` derives the October 3 recommendation only from a validated conformance report. It rejects altered counts, duplicate IDs and unsupported promotion of blocked Fidelity checks. The result separates synthetic evidence acceptance, Fidelity deferral, fallback progression and release authority; both founder approval and release authorization are hard-coded false.

September 27 afternoon: `atlas.conformance` defines a public-safe, versioned M1 evidence map with unique check IDs and controlled statuses. The `/m1-status` view renders that model without accepting input or recording acceptance. Synthetic verification, unavailable Fidelity evidence and unimplemented private persistence remain distinct states; the aggregate is `partial_synthetic_only`, so UI wording cannot promote synthetic tests into broker compatibility.

September 27 M1 workflow increment: `atlas.import_workflow` now owns exact-byte hashing, synthetic CSV parsing, reconciliation, replay gating and redacted receipt creation for both CLI and preview adapters. The local `/import-demo` route invokes that shared workflow only for the checked-in invented fixture. It accepts no upload, query, source path or account connection and persists nothing; its `replay_check_required` result demonstrates why reconciliation alone is insufficient for safe publication.

September 16 afternoon: `assess_metric_input` composes metadata eligibility with selected-observation payload binding and numeric availability; blocked results release no value. Existing metadata-only API remains unchanged. Source accuracy, fiscal-calendar validation and persistence remain pending.

September 16: `atlas.metric_evidence` binds versioned metric definitions/Decimal values and reporting-period dates to canonical payload hashes checked against observation metadata. It detects payload/version/date drift but does not authenticate sources. Automatic readiness integration, persistence and fiscal-period alignment remain pending.

September 15 metric increment: `atlas.metrics` defines immutable semantic versions and finite Decimal/unavailable values, rejecting incompatible same-definition comparisons. See [metric contract](METRICS.md). Value-to-provenance hash binding and readiness integration remain pending; no formula text is executed.

September 15 navigation increment, extended September 27: the local preview uses an exact route allowlist: `/overview` for the fixed five-area page, `/` for the kernel-backed put form, `/import-demo` for the checked-in synthetic CSV receipt, `/m1-status` for the public-safe M1 evidence boundary, and `/checklist` for escaped read-only acceptance instructions. It does not serve caller-selected files or directory listings. The downloadable offline page remains standalone; the interactive link is inserted only when served locally. This is still synthetic UX-01 work, not the integrated R13 application.

## Offline UX preview boundary — September 14

`product/preview/index.html` is a standalone, fixed synthetic navigation/disclosure prototype for UX-01. It contains no JavaScript, financial input form, backend integration, persistence or remote dependencies; CSP denies network resources and form submission. This is not the planned authenticated UI described below. `atlas.preview.synthetic_preview_model` calculates the checked-in values through `atlas.risk`, and a regression test requires the HTML values to agree. The page does not invoke Python at runtime. Browser/device QA and founder workflow validation remain separate from structural and value-contract checks.

`atlas.web_preview` is the first interactive slice: a standard-library HTTP server bound exclusively to `127.0.0.1`. It uses a per-process form token, strict body/field limits, host/path/content-type checks, no-store and restrictive browser headers, no request logging, and no persistence. A form submission calls the existing deterministic `standard_option_payoff`; the read-only import route calls the shared synthetic import workflow with the repository fixture. Neither can access customer accounts, caller-selected files, market data or orders. This temporary founder-feedback adapter is not the future API/authentication architecture and must not be exposed to a network or reused as production security.

## ADR-001: modular monolith, deterministic core

Proposed architecture: Python calculation/research core, API, relational database, object storage for immutable source snapshots, job worker, and browser UI. Start with a modular monolith to simplify transactions, deployment and debugging. Select and pin framework versions when implementation begins. Do not install the legacy broad dependency list for this product.

Modules: profile/consent; account import/reconciliation; security master; provider adapters; financial normalization; research/signals; portfolio/risk; options scenarios; backtests/paper ledger; report generation; audit/jobs; API/UI. Broker execution is outside prototype scope and has no callable implementation.

Data flow: source adapter → immutable source record → validation/reconciliation → normalized point-in-time dataset → deterministic calculation → research evidence record → private report. A failed validation prevents a complete/recommendation-ready status. Provider unavailability must become a visible gap, not fabricated data.

Current implementation includes `atlas.risk`, a local risk CLI, the `atlas.ingestion` versioned envelope/reconciliation interface, an explicit source-adapter protocol, an optional hash-only local SQLite replay ledger, a profile-driven synthetic broker-shaped mapping harness with a bounded CSV boundary, a shared synthetic import/receipt workflow used by CLI and local preview, and `atlas.reference` effective-dated identity/data-rights gates. The harness guarantees one mapping outcome per invented source row; its immutable profile explicitly declares headers, row/footer semantics, currency and exact rounding, and remains labeled unvalidated for Fidelity. See the [import contract](IMPORT_CONTRACT.md) and [security-master contract](SECURITY_MASTER.md). Database, API, UI, populated reference data, production audit storage, real broker-specific account adapters and jobs remain planned.

## ADR-004: labels do not establish identity or permission

Resolve a security from stable issuer/instrument IDs plus exchange MIC, symbol and effective period. A symbol match is insufficient; missing and overlapping identities block downstream research. Keep display names mutable and sourced. Independently gate each provider dataset by intended use using latest reviewed evidence. Identity resolution does not imply data rights, and data rights do not verify security identity. This separation prevents a valid ticker from laundering unlicensed data—or licensed data from being attached to the wrong security.

## ADR-002: account access boundary

Use redacted exports first. Fidelity integration must use an authorized data-sharing provider and user consent; never collect Fidelity passwords or scrape logged-in accounts. Fidelity describes secure third-party data-sharing controls here: https://www.fidelity.com/security/third-party-app-protection (reviewed September 12, 2026). This does not establish that our app has provider access, an agreement, or production rights.

MyInvestor's exposed catalog is useful for security discovery; it is not a Fidelity account connector. InvestmentIQ's exposed calculator projects growth using user-supplied assumptions; it is not a brokerage feed, stock forecasting model or backtest engine. Do not embed either connector's data in a commercial product without verifying terms and redistribution rights.

## Current snapshot input contract

```json
{
  "schema_version": 1,
  "mode": "user_export",
  "currency": "USD",
  "as_of": "2026-09-12T00:00:00+00:00",
  "cash": "5000",
  "positions": [
    {"symbol": "DEMO", "asset_type": "equity", "quantity": "100", "price": "50"}
  ]
}
```

This is a normalized JSON contract, not a Fidelity CSV parser. `DEMO` is synthetic. Use decimal strings for money/quantity; no floats, negative balances, short positions, options, FX or duplicate symbols. Dates must be aware, not future and within four days by default; this snapshot threshold is not a live option-quote freshness policy. Never remove unsupported positions to make an incomplete portfolio look complete. A current price is not independently verified by this kernel.

Planned importer records account alias, instrument stable ID, quantity, price/as-of, market value, cash/core fund semantics, cost basis if present, source file hash, import version and row outcomes. Reconcile both per-account and aggregate totals; avoid counting a core money-market holding and cash twice. The implemented local ledger makes exact normalized-file replays idempotent at the publication boundary and detects source-ID/content conflicts; it is not the planned multi-tenant audit store. Persist raw files only in an approved private store. Handle unsettled transactions, pending activity, corporate actions, short positions and option symbology explicitly.

## Research record

The implemented `atlas.provenance` contract binds stable instrument/provider/dataset/metric IDs to an as-of date, revision, source and payload hashes, versioned transform, `available_at` and `observed_at`. Historical selection excludes revisions unavailable at the decision time and preserves amendments rather than overwriting historical knowledge. Its combined gate releases an observation reference only when point-in-time selection, effective instrument identity and current purpose-specific data rights all pass. `atlas.source_evidence` then verifies that the selected observation agrees with one exact source-document record before the sourced-metric gate releases a value. See [point-in-time provenance](PROVENANCE.md) and [research source contract](RESEARCH_SOURCE_CONTRACT.md).

Still planned: persistent values, currency/units, confidence/quality flags and a result record containing input hashes, configuration, code commit, metric definitions, output and validation state. Current `ready` means contract-eligible only; metric-quality, source-accuracy and research-validation gates remain separate.

## ADR-003: evidence before complex models

Compare buy-and-hold, simple momentum and simple valuation/quality baselines before ML. The existing root preprocessing fits normalization on the full series and the trainer uses random splits, so legacy accuracy is not accepted as trading evidence. Keep that experiment isolated. LLMs may extract and summarize cited evidence; they cannot be the authoritative calculator or override risk limits. Treat external text as untrusted data and protect against prompt injection.

## Planned operations and cost controls

Jobs use unique run keys, transactional state, bounded retries, deduplication and dead-letter review. Market jobs respect exchange calendars and daylight-saving time; executive reports use Asia/Manila. Separate ingestion as-of from report generation time. Define alert routes before enabling them.

Proposed private-prototype objectives, pending measurement: import of 1,000 rows under 10 seconds; weekly batch completes within 30 minutes; recovery point within 24 hours and restoration within 4 hours. These are targets, not measured results or customer SLAs. Budget approval is needed before paid hosting or data. Always retain a local synthetic demo path.
