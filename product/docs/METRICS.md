# Metric semantics contract — September 15, 2026

## Combined metric gate — September 16 afternoon

`assess_metric_input` first runs the existing point-in-time, security identity and current purpose-specific rights gate, then verifies the supplied payload against the selected observation and requires a numeric value. Blocked results contain codes but no payload or observation ID. Malformed requests raise ValueError. The original metadata-only API retains its meaning.

This connects the binding contract to research eligibility. It does not establish source accuracy, fiscal-calendar correctness, freshness appropriate to every metric, investment merit or provider access. No populated dataset, screen or persisted results are added. Six integration cases cover success, missing dependencies/permission, altered values, bound missing values, revision leakage and invalid payloads.

## Evidence binding — September 16

`atlas.metric_evidence.MetricPayload` binds a metric value and full definition to explicit inclusive reporting start/end dates. V1 canonical UTF-8 JSON uses sorted keys, compact separators, schema_version=1 and the exact Decimal string (123.40 differs from 123.4). SHA-256 covers all these fields, including missing reason and definition version. It is not a signature, anonymization or proof of source accuracy.

`verify_metric_binding` rejects differing metric IDs, transformation versions, period-end/as-of dates or payload hashes against an `ObservationRecord`. Original and revised observations retain distinct hashes for point-in-time selection. Missing values can have valid evidence bindings; this does not make them usable numeric operands.

Start must not follow end; instant metrics require one date. Quarter/year/TTM calendar duration, fiscal calendars and comparisons across actual date windows still require reviewed adapters. No persistence, real source population, automated research-readiness integration or new UI is delivered by this increment. This binding verifies claimed payload integrity only; identity, rights, availability and financial semantics remain separate gates.

`atlas.metrics` provides immutable versioned definitions and Decimal values. Definitions include metric ID, definition version, human-readable formula, unit, currency, period, null policy and exact transformation version. It does not execute formula text.

Current units: money, money_per_share, ratio (fraction, not percent) and count. Monetary units require USD; dimensionless/count values require absent currency. Period labels are instant, quarter, annual and ttm. Labels do not prove actual date alignment or correct aggregation. No FX, scale conversion or annualization is performed implicitly.

Values must be finite Decimal numbers or explicitly unavailable. Zero and negative numbers are retained. Missing source is not zero; a not-meaningful value requires a definition permitting that state. Negative-base growth must be marked not meaningful by the future calculation adapter, not invented by this contract.

`require_compatible` blocks missing operands and any difference in the full definition, including formula and transformation version. It is a precondition for same-definition comparisons, not a formula engine: different metrics needed for ratios must eventually use individually reviewed calculation contracts rather than bypass this check.

Limits: no sourced catalog, numeric observation storage, point-in-time value/hash binding, readiness-gate integration, period-start/end alignment, sector formulas, provider adapter or investment signal exists here. Passing this contract does not make an observation research-ready. Separate provenance/identity/rights gates still apply.

Founder M2 verification: trace a displayed metric to its definition/source; check USD/unit, reporting dates, formula and version. Try missing and incompatible-quarter/TTM fixtures; expect no comparative result. This session ships the backend contract only, not that future screen or M2 acceptance.
