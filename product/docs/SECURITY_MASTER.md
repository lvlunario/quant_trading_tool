# Security master and data-rights contract

Requirement R06; [tracking issue #4](https://github.com/lvlunario/quant_trading_tool/issues/4). This foundation defines fail-closed identity and permission decisions. It does **not** populate or verify the requested watchlist, grant a data license, or authorize commercial use.

## Effective-dated security identity

`SecurityRecord` separates identifiers from labels:

- `issuer_id`: stable Atlas issuer identity; `issuer_name` is a sourced display label that may change.
- `instrument_id`: stable security/class identity; never derive it from a ticker.
- `symbol`, ISO 10383-style four-character exchange MIC and half-open effective period `[effective_from, effective_to)`.
- USD currency and an explicit class: common, preferred, depositary receipt, fund or other listed.
- HTTPS evidence URI and timezone-aware observation time.

`resolve_security(records, symbol, exchange_mic, on_date)` returns `resolved`, `missing` or `ambiguous`. A ticker may be reused by different instruments in non-overlapping periods. Overlapping identities are ambiguous; future-dated evidence and reuse of an instrument ID across issuer/class identities fail validation. The resolver never substitutes a similar ticker.

Names and ticker labels are not identity. This matters for symbol changes, listings on multiple venues, corporate actions and historical backtests: a present-day ticker lookup cannot safely identify what a historical row represented.

The repository contains synthetic tests only. It intentionally does not seed NVDA, MU, QCOM, PLTR, SPCX, QBTS or RGTI until records are sourced and reviewed. `CRBS` is explicitly tested as `missing`; its intended issuer remains a founder decision and no substitute is inferred.

## Dataset permission evidence

`DataRightsRecord` stores an opaque provider/dataset ID, review status, explicitly permitted uses, HTTPS terms URI, SHA-256 of the reviewed evidence, review time and optional expiry. Supported use cases are separately gated:

| Use | Meaning |
|---|---|
| `internal_research` | Private analysis not shown to customers |
| `customer_display` | Data or derived content displayed in the private product |
| `model_training` | Provider data used to fit or tune a model |
| `redistribution` | Raw or derived data distributed beyond the licensed application |

`check_data_rights` selects the latest applicable evidence. Missing, pending, expired, prohibited, ambiguous or non-permitted use returns a distinct blocked decision. A `verified` record must list at least one explicit use; pending/prohibited records cannot carry permissions. Evidence hashes establish which terms were reviewed, not that Atlas owns a license or that counsel approved an interpretation.

## Population and review plan

1. Verify issuer, security class, exchange MIC and symbol interval using primary issuer/exchange/regulatory evidence.
2. Obtain and archive provider terms privately; record a hash and review date without copying restricted terms into the public repository.
3. Evaluate each intended use independently. Default every unreviewed combination to blocked; no paid provider is approved.
4. Record corporate actions and identifier changes as new effective-dated evidence instead of overwriting history.
5. Before customer use, add persistent private storage, controlled updates, four-eyes review, provenance exports, retention and periodic rights revalidation.

Still pending: primary-source population, CUSIP/ISIN/FIGI policy and licensing, corporate-action ingestion, provider selection, qualified legal review, persistence and customer-facing integration.

Observation records reference these stable instrument/provider/dataset IDs but do not bypass either gate; see [point-in-time provenance](PROVENANCE.md).
