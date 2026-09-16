# Normalized import contract — synthetic implementation

Requirement R04; [tracking issue #2](https://github.com/lvlunario/quant_trading_tool/issues/2). This is the reconciliation boundary a future broker-specific adapter must satisfy, not a claim of Fidelity compatibility.

The JSON envelope is strict and versioned: `schema_version: 1`; `mode` matched to `source_type`; `currency: USD`; opaque `source_id` matching `SRC_` plus 8–32 uppercase letters/digits; timezone-aware `as_of`; independent `expected_totals`; and normalized `rows`. Default freshness is four days. Unknown fields, future/naive/stale timestamps, other currencies and mode/source mismatches fail before reconciliation.

```python
from atlas.ingestion import ImportRow, reconcile

result = reconcile([
    ImportRow('ACCT_ALPHA', 'equity', 'DEMO', '2.5', '10', '25'),
    ImportRow('ACCT_ALPHA', 'cash', '', '0', '0', '75'),
], {'ACCT_ALPHA': '100'})
assert result.status == 'reconciled'
```

All values above are invented. No raw account number field exists. Aliases use `ACCT_` followed by 1–16 uppercase letters. Values use nonnegative decimal strings, up to 15 integer digits and 8 decimal places; floats, exponent notation, negative values and nonfinite values are rejected. Computation uses a local Decimal precision of 80, independent of a caller's precision setting.

Supported rows: positive long-equity quantity/price, cash, or already normalized core cash. Cash uses blank symbol and zero quantity/price; market_value is its balance. Adapters, not this module, must establish when a core fund represents cash. Cash and core cash together for an account are rejected rather than assumed additive. Duplicate symbols within an account reject all copies; the same symbol across separate accounts is valid. Lot aggregation is not implemented.

Callers supply independent per-account USD totals. Equity quantity × price must exactly equal its reported market value. Accepted row sums must exactly match all expected account totals. No tolerance is silently applied; broker price/cent rounding needs a separately specified adapter policy. Account coverage includes missing accounts, not just accounts that happen to parse.

Every input row gets a 1-based row number, accepted/rejected status and a safe reason code. Any invalid row, unsupported asset (including options), coverage gap or total mismatch returns `blocked` with empty published rows and account totals. Individual `accepted` outcomes mean that row passed checks, not that the whole import is usable. Errors never echo raw values. A reconciled result still contains sensitive positions and must remain private when used with real input.

Envelope failures (empty/oversized row list, missing totals, invalid expected aliases/amounts) raise ValueError before row processing. Maximum 10,000 rows. The pure function makes no writes and is deterministic on identical inputs; this is not durable duplicate-import suppression. A transactional persistence layer must eventually own import IDs, hashes and replay rules.

The local `--reconcile` CLI sends exact source bytes through the `PortfolioSourceAdapter` boundary. Its only implementation, `NormalizedJsonAdapter`, accepts a UTF-8 object already using this contract and independently enforces the 1 MB limit. No Fidelity column mapping is implemented. The CLI emits metadata, safe row outcomes, totals, count, readiness and an exact-source SHA-256—but no symbols, quantities or prices. Exit code 0 means reconciled, 3 means safely blocked, and 2 means invalid input.

`--ledger /private/path/import-audit.sqlite3` enables an atomic local SQLite replay gate. It stores only source ID, SHA-256, reconciliation outcome and first-seen UTC time, creates a new file with owner-only permissions, and rejects an existing file accessible by group/others. The same ID, digest and outcome is an `exact_replay`; its publishable row count becomes zero. Reusing an ID with different bytes, reusing bytes under another ID, or changing the recorded outcome fails closed. A digest links identical content and is **not anonymization**; ledger and CLI output remain private. Without `--ledger`, replay status is `not_checked` and durable suppression is absent. Consumers may persist rows only when reconciliation succeeds and replay status is `recorded` (or under a separately controlled first-import path).

Still pending: Fidelity CSV mapping; reconciliation rounding policy; real export validation; production audit storage; concurrency/load qualification; options and unsettled activity. Do not use this arithmetic boundary alone to establish a complete brokerage portfolio.
