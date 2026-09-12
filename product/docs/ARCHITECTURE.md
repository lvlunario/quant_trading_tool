# Architecture and decisions

## ADR-001: modular monolith, deterministic core

Proposed architecture: Python calculation/research core, API, relational database, object storage for immutable source snapshots, job worker, and browser UI. Start with a modular monolith to simplify transactions, deployment and debugging. Select and pin framework versions when implementation begins. Do not install the legacy broad dependency list for this product.

Modules: profile/consent; account import/reconciliation; security master; provider adapters; financial normalization; research/signals; portfolio/risk; options scenarios; backtests/paper ledger; report generation; audit/jobs; API/UI. Broker execution is outside prototype scope and has no callable implementation.

Data flow: source adapter → immutable source record → validation/reconciliation → normalized point-in-time dataset → deterministic calculation → research evidence record → private report. A failed validation prevents a complete/recommendation-ready status. Provider unavailability must become a visible gap, not fabricated data.

Current implementation is only `atlas.risk` and a local CLI. Database, API, UI, production audit storage, account adapters and jobs remain planned.

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

Planned importer records account alias, instrument stable ID, quantity, price/as-of, market value, cash/core fund semantics, cost basis if present, source file hash, import version and row outcomes. Reconcile both per-account and aggregate totals; avoid counting a core money-market holding and cash twice. Duplicate exports must be idempotent. Persist raw files only in an approved private store. Handle unsettled transactions, pending activity, corporate actions, short positions and option symbology explicitly.

## Planned research record

Entity ID, effective symbol, provider, document/filing URL, observed_at, available_at, accounting period, vintage, currency, original and normalized values, transform version, confidence/quality flags. Result record contains input hashes, configuration, code commit, metric definitions, output and validation state. Preserve amendments rather than overwriting historical knowledge.

## ADR-003: evidence before complex models

Compare buy-and-hold, simple momentum and simple valuation/quality baselines before ML. The existing root preprocessing fits normalization on the full series and the trainer uses random splits, so legacy accuracy is not accepted as trading evidence. Keep that experiment isolated. LLMs may extract and summarize cited evidence; they cannot be the authoritative calculator or override risk limits. Treat external text as untrusted data and protect against prompt injection.

## Planned operations and cost controls

Jobs use unique run keys, transactional state, bounded retries, deduplication and dead-letter review. Market jobs respect exchange calendars and daylight-saving time; executive reports use Asia/Manila. Separate ingestion as-of from report generation time. Define alert routes before enabling them.

Proposed private-prototype objectives, pending measurement: import of 1,000 rows under 10 seconds; weekly batch completes within 30 minutes; recovery point within 24 hours and restoration within 4 hours. These are targets, not measured results or customer SLAs. Budget approval is needed before paid hosting or data. Always retain a local synthetic demo path.
