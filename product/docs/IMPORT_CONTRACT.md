# Normalized import contract — synthetic implementation

Requirement R04; [tracking issue #2](https://github.com/lvlunario/quant_trading_tool/issues/2). This is the reconciliation boundary a future broker-specific adapter must satisfy, not a claim of Fidelity compatibility.

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

Still pending: Fidelity CSV mapping; file parsing/limits; source hash and timestamps; freshness/currency validation at the import-envelope level; reconciliation rounding policy; real export validation; options and unsettled activity; durable ledger; connection to the risk CLI. Do not use this arithmetic boundary alone to establish a complete or current brokerage portfolio.
