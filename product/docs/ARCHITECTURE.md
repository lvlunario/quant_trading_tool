# Architecture and decisions

September 15 navigation increment: the local preview uses an exact route allowlist: `/overview` for the fixed five-area page, `/` for the kernel-backed put form, and `/checklist` for escaped read-only acceptance instructions. It does not serve caller-selected files or directory listings. The downloadable offline page remains standalone; the interactive link is inserted only when served locally. This is still synthetic UX-01 work, not the integrated R13 application.

## Offline UX preview boundary — September 14

`product/preview/index.html` is a standalone, fixed synthetic navigation/disclosure prototype for UX-01. It contains no JavaScript, financial input form, backend integration, persistence or remote dependencies; CSP denies network resources and form submission. This is not the planned authenticated UI described below. `atlas.preview.synthetic_preview_model` calculates the checked-in values through `atlas.risk`, and a regression test requires the HTML values to agree. The page does not invoke Python at runtime. Browser/device QA and founder workflow validation remain separate from structural and value-contract checks.

`atlas.web_preview` is the first interactive slice: a standard-library HTTP server bound exclusively to `127.0.0.1`. It uses a per-process form token, strict body/field limits, host/path/content-type checks, no-store and restrictive browser headers, no request logging, and no persistence. A form submission calls the existing deterministic `standard_option_payoff`; it cannot access accounts, market data or orders. This temporary founder-feedback adapter is not the future API/authentication architecture and must not be exposed to a network or reused as production security.

## ADR-001: modular monolith, deterministic core

Proposed architecture: Python calculation/research core, API, relational database, object storage for immutable source snapshots, job worker, and browser UI. Start with a modular monolith to simplify transactions, deployment and debugging. Select and pin framework versions when implementation begins. Do not install the legacy broad dependency list for this product.

Modules: profile/consent; account import/reconciliation; security master; provider adapters; financial normalization; research/signals; portfolio/risk; options scenarios; backtests/paper ledger; report generation; audit/jobs; API/UI. Broker execution is outside prototype scope and has no callable implementation.

Data flow: source adapter → immutable source record → validation/reconciliation → normalized point-in-time dataset → deterministic calculation → research evidence record → private report. A failed validation prevents a complete/recommendation-ready status. Provider unavailability must become a visible gap, not fabricated data.

Current implementation includes `atlas.risk`, a local risk CLI, the `atlas.ingestion` versioned envelope/reconciliation interface, an explicit source-adapter protocol, an optional hash-only local SQLite replay ledger, and `atlas.reference` effective-dated identity/data-rights gates. See the [import contract](IMPORT_CONTRACT.md) and [security-master contract](SECURITY_MASTER.md). Database, API, UI, populated reference data, production audit storage, broker-specific account adapters and jobs remain planned.

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

The implemented `atlas.provenance` contract binds stable instrument/provider/dataset/metric IDs to an as-of date, revision, source and payload hashes, versioned transform, `available_at` and `observed_at`. Historical selection excludes revisions unavailable at the decision time and preserves amendments rather than overwriting historical knowledge. Its combined gate releases an observation reference only when point-in-time selection, effective instrument identity and current purpose-specific data rights all pass. See [point-in-time provenance](PROVENANCE.md).

Still planned: persistent values, currency/units, confidence/quality flags and a result record containing input hashes, configuration, code commit, metric definitions, output and validation state. Current `ready` means contract-eligible only; metric-quality, source-accuracy and research-validation gates remain separate.

## ADR-003: evidence before complex models

Compare buy-and-hold, simple momentum and simple valuation/quality baselines before ML. The existing root preprocessing fits normalization on the full series and the trainer uses random splits, so legacy accuracy is not accepted as trading evidence. Keep that experiment isolated. LLMs may extract and summarize cited evidence; they cannot be the authoritative calculator or override risk limits. Treat external text as untrusted data and protect against prompt injection.

## Planned operations and cost controls

Jobs use unique run keys, transactional state, bounded retries, deduplication and dead-letter review. Market jobs respect exchange calendars and daylight-saving time; executive reports use Asia/Manila. Separate ingestion as-of from report generation time. Define alert routes before enabling them.

Proposed private-prototype objectives, pending measurement: import of 1,000 rows under 10 seconds; weekly batch completes within 30 minutes; recovery point within 24 hours and restoration within 4 hours. These are targets, not measured results or customer SLAs. Budget approval is needed before paid hosting or data. Always retain a local synthetic demo path.
