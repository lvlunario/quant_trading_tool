# M1 import conformance — September 27, 2026

Status: **partial synthetic-only**. This is an engineering evidence summary, not a completed meeting, founder acceptance, Fidelity compatibility or release authorization.

## Demonstration

From `product/`, run `python -m atlas --preview-server`, open the displayed localhost overview, then choose **Run fixed synthetic import demo** and **View M1 conformance** from Portfolio.

The import demo processes only the checked-in invented fixture. The conformance view is generated from `atlas.conformance.m1_import_conformance`; it accepts no input and stores no response.

## Verified with synthetic evidence

| Check | Evidence | Limitation |
|---|---|---|
| Every source record receives an outcome | Malformed and unsupported-row tests | Real Fidelity row types have not been observed |
| Positions and account totals reconcile exactly | Cash, equity and mismatch tests | Source-specific rounding is unknown |
| Exact retries cannot republish through the private ledger | First-attempt and exact-replay tests | Browser demo intentionally has no persistence |
| UI receipt excludes financial/account fields | Receipt allowlist and HTTP privacy tests | Minimization is not anonymization |

## Blocked on external evidence

| Check | Missing evidence | Required before acceptance |
|---|---|---|
| Fidelity headers, footers and row classifications | Representative authorized export | Private format review and versioned profile |
| Fidelity cash/core semantics | Representative authorized export | Explicit cash/core classification |
| Fidelity option symbols and unsettled activity | Representative authorized export | Supported/blocked row rules and tests |
| Fidelity valuation/rounding | Representative authorized export | Documented source-specific reconciliation policy |

Private import persistence is **not implemented**. The destination policy is selected, but a private repository/storage boundary has not been provisioned.

## October 3 disposition rule

- Accept only the synthetic import-contract scope if all automated evidence remains green.
- Do not label M1 Fidelity-compatible without authorized representative-export evidence.
- If the private boundary or export remains unavailable, record Fidelity validation as deferred and proceed with the synthetic/manual-redacted fallback; do not move the December stabilization window.
- Browser visual/accessibility QA remains a separate open acceptance item.

## Verification

Expected automated result: 144 tests, including conformance status/count integrity and HTTP privacy rendering. Exact feature commit and CI evidence are recorded in the September 27 daily log and PR #1.

Founder decision: **Pending**. No response or approval is inferred from this packet.
