# Macroeconomic release and vintage contract

Status: implemented with synthetic tests on September 28, 2026. No real macro
series, provider adapter or licensed dataset is populated.

## Purpose

Economic data is often revised. A backtest or historical report must use the
value that was available at its decision time—not the latest revised value now
visible in a database.

`atlas.macro_vintages.MacroReleaseRecord` stores each published vintage as a
separate immutable record with:

- stable macro-series, provider and dataset IDs;
- reporting period, frequency, unit and seasonal-adjustment policy;
- revision number, availability and observation timestamps;
- finite Decimal value or an explicit missing reason;
- HTTPS source URI, exact-byte SHA-256 and transform version.

Macro series use their own `MAC_...` identity. They are not attached to a fake
security or ticker.

## Selection and readiness

`select_macro_vintage` chooses only the latest revision available at the
requested decision timestamp. It blocks future decisions/observations,
duplicate or backward revisions, conflicting series semantics and unknown
series/periods.

`assess_macro_input` then applies the existing purpose-specific data-rights
gate. Missing values remain missing and are never converted to zero. A ready
result means only that point-in-time selection and the recorded rights evidence
passed; it is not an economic forecast or claim that the source is accurate.

## Current limits

- Synthetic records only; no FRED, BLS, BEA, Federal Reserve or commercial
  adapter is implemented or licensed by this contract.
- Source authenticity, calendar expectations, unit scaling, seasonal-method
  changes, cross-series transformations and persistence remain separate work.
- Research UI, causal exposure mapping and regime interpretation remain planned.

## Verification

Tests cover original-versus-revised selection, unavailable/unknown periods,
rights gating, explicit missing values, duplicate/backward revisions, semantic
conflicts, future evidence and invalid record fields.

