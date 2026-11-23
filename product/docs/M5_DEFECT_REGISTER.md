# M5 public-safe defect register

Opened November 19, 2026 for the reduced local/synthetic release-candidate
rehearsal. This register contains no private account data, credentials, source
review evidence or personal reports.

## Register state

- Review status: `opened_not_completed`
- Recorded defects: **0**
- Critical-defect status: `unknown_pending_formal_review`
- Independent review completed: **no**
- Automated rehearsal execution failures: **0**
- Zero-defect conclusion: **not supported**

Zero recorded defects means no entry has yet been filed against this candidate.
It does not mean that no critical calculation, privacy, security or usability
defect exists. The exact November 28 build does not exist yet, and independent
review plus founder UAT have not occurred.

## Entry contract

Every future defect row must include:

| Field | Required content |
|---|---|
| Defect ID | Stable public-safe identifier |
| Observed at | Asia/Manila timestamp and exact candidate commit/build |
| Severity | Critical, high, medium or low with rationale |
| Affected workstream | One of the four frozen candidate workstreams |
| Reproduction | Synthetic or disposable steps only |
| Expected / actual | Verifiable behavior without private values |
| Evidence | Test, log reference or screenshot that contains no secrets |
| Status | Open, fixed, retest passed, deferred or not reproducible |
| Release effect | Block, review required or non-blocking |

Incorrect portfolio/risk arithmetic, privacy exposure, order-path enablement or
unauthorized data access is release-blocking regardless of test count.

## Recorded defects

No defect entries are recorded yet. The November 19 automated rehearsal
completed all four public-safe workstreams without an execution failure, but it
is pre-freeze evidence rather than a critical-defect review.

## Known limitations are not defect closures

- Fidelity compatibility remains unverified pending an authorized
  representative export ([issue #2](https://github.com/lvlunario/quant_trading_tool/issues/2)).
- Private persistence and recovery remain unimplemented; the inherited
  environment file still needs private owner review
  ([issue #3](https://github.com/lvlunario/quant_trading_tool/issues/3)).
- Licensed sourced research remains blocked pending rights and dataset evidence
  ([issue #4](https://github.com/lvlunario/quant_trading_tool/issues/4)).
- Managed authentication, log-redaction evidence, independent security review
  and founder UAT remain incomplete.

These limitations constrain the candidate scope. They must not be converted
into fabricated defects, closures, approvals or compatibility claims.
