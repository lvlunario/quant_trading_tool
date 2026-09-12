# Requirements and analytics inventory

Statuses as of foundation: IMPLEMENTED means local kernel only; PLANNED is not available.

| ID | Requirement | Acceptance | Status |
|---|---|---|---|
| R01 | Explicit input mode, schema, USD, timezone and freshness | Reject stale/future/naive snapshots, unsupported currencies and assets | IMPLEMENTED |
| R02 | Long-equity snapshot value/concentration with Decimal | Hand-calculated fixtures and invalid-data rejection pass | IMPLEMENTED |
| R03 | Standard covered-call/CSP expiry scenario arithmetic | Bankruptcy, upside cap, breakeven, coverage and reserve cases pass | IMPLEMENTED |
| R04 | Fidelity export importer | Reconcile balances and positions; report all rejected rows; no silent omission | PLANNED |
| R05 | Customer mandate | Capture goals, horizon, liquidity, account types, tax context, loss tolerance, experience and restrictions | PLANNED |
| R06 | Security master and provenance | Issuer, exchange, currency, class, stable ID, symbol effective dates, source time | PLANNED |
| R07 | Fundamentals and qualitative thesis | Point-in-time metrics plus citations, counter-thesis and missing-data markers | PLANNED |
| R08 | Macro and market regime | Release/vintage dates and causal exposure mapping; no certainty from regimes | PLANNED |
| R09 | Equity strategy testing | Chronological walk-forward, costs, benchmark alignment and holdout | PLANNED |
| R10 | Options research | Executable chain freshness, liquidity, IV/Greeks, expiry, earnings/dividend and assignment risks | PLANNED |
| R11 | Portfolio risk | Total exposures incl. options, correlation, stress, drawdown, factor and concentration limits | PLANNED |
| R12 | Weekly research report | Data as-of, changes, ranked candidates, thesis risks, blocked items, next checks | PLANNED |
| R13 | Private customer application | Authentication, consent, access isolation, deletion/export and audit logs | PLANNED |
| R14 | Operations | Idempotent jobs, retries, monitoring, backup/restore and rollback | PLANNED |
| R15 | Reproducible evidence | Versioned data references, config, code SHA, result checksums and experiment registry | PLANNED |
| R16 | Commercial gate | Counsel, independent security review, licensing and founder acceptance | PLANNED |

## Research universe

Requested symbols: NVDA, MU, QCOM, PLTR, SPCX, CRBS, QBTS, RGTI. Treat this as a watchlist request, not current holdings or endorsed candidates. MyInvestor catalog lookup on September 12 returned SPCX as Space Exploration Technologies class A on XNAS, but no CRBS match. Preserve this as provider-reported discovery, not verified exchange history. Confirm CRBS's intended issuer and verify all securities using primary exchange/issuer records before production. Do not silently substitute CRSP or another symbol. New listings and symbol reuse require effective-dated identifiers and explicit insufficient-history flags.

## Metric dictionary scope

| Domain | Candidate metrics/content | Controls |
|---|---|---|
| Growth | Revenue/EPS/FCF growth, organic vs acquired, segment growth, revisions | Period alignment; negative-base growth marked NM |
| Quality | Gross/operating/net margin, ROIC, ROE, accruals, cash conversion, SBC/dilution | Reported vs adjusted separated; reconcile non-GAAP |
| Value | P/E, EV/EBITDA, EV/sales, FCF yield, DCF ranges and peer comps | Negative earnings/FCF marked NM; enterprise/equity consistency |
| Balance sheet | Net debt, leverage, coverage, maturities, liquidity, runway | Sector-specific interpretation and dated sources |
| Technical | Total-return momentum, moving averages, breakout levels/volume, relative strength, realized volatility | Corporate actions, lagged signals and no same-bar fills |
| Options | Bid/ask, spread, volume/OI, IV surface/rank/percentile, Greeks, skew, term structure | Timestamp and method; delta is not a guaranteed probability |
| Portfolio | Weights, sector/factor/beta, correlation, cash, drawdown, VaR/CVaR, stress | Coverage completeness; tail-model limitations |
| Macro | Inflation, labor, rates/curve, growth, credit spreads, USD, liquidity | Release calendar and original data vintage |
| Qualitative | Moat, management, governance, customer concentration, competition, regulation, catalysts | Cited evidence vs judgment, counterarguments, prove/kill triggers |

Prioritize a validated subset over an unbounded promise to analyze every metric. Every metric definition needs formula, units, period, source, as-of/available-at times, null handling and QA. Sector adapters matter: semiconductor cycles/inventory/capex differ from unprofitable quantum companies' runway and dilution risks.

## Customer intake and suitability boundary

Capture investment objective and benchmark; investment horizon; near-term cash needs; loss capacity versus emotional tolerance; current allocation and outside exposures; account types; tax jurisdiction and cost-basis availability; options approval/experience; liquidity and position restrictions. Unknown values remain unknown. Before proposing limits, ask the founder to approve a policy. Never infer current assets, buying power or holdings from prior conversation estimates.

Income is not equivalent to total return. A high premium does not make an option safe. Display assignment obligations, capped upside, downside to zero, concentration after assignment and fees before ranking premium yield. The Options Industry Council describes CSP downside as substantial if the underlying falls: https://www.optionseducation.org/strategies/all-strategies/cash-secured-put (reviewed September 12, 2026).
