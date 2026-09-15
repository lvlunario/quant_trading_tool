# Metric semantics contract — September 15, 2026

`atlas.metrics` provides immutable versioned definitions and Decimal values. Definitions include metric ID, definition version, human-readable formula, unit, currency, period, null policy and exact transformation version. It does not execute formula text.

Current units: money, money_per_share, ratio (fraction, not percent) and count. Monetary units require USD; dimensionless/count values require absent currency. Period labels are instant, quarter, annual and ttm. Labels do not prove actual date alignment or correct aggregation. No FX, scale conversion or annualization is performed implicitly.

Values must be finite Decimal numbers or explicitly unavailable. Zero and negative numbers are retained. Missing source is not zero; a not-meaningful value requires a definition permitting that state. Negative-base growth must be marked not meaningful by the future calculation adapter, not invented by this contract.

`require_compatible` blocks missing operands and any difference in the full definition, including formula and transformation version. It is a precondition for same-definition comparisons, not a formula engine: different metrics needed for ratios must eventually use individually reviewed calculation contracts rather than bypass this check.

Limits: no sourced catalog, numeric observation storage, point-in-time value/hash binding, readiness-gate integration, period-start/end alignment, sector formulas, provider adapter or investment signal exists here. Passing this contract does not make an observation research-ready. Separate provenance/identity/rights gates still apply.

Founder M2 verification: trace a displayed metric to its definition/source; check USD/unit, reporting dates, formula and version. Try missing and incompatible-quarter/TTM fixtures; expect no comparative result. This session ships the backend contract only, not that future screen or M2 acceptance.
