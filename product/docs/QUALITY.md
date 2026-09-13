# Research, QA and release quality

## Verification levels

1. Unit: independent expected values for money, weights and expiry payoffs; invalid-input cases.
2. Contract: provider schemas, missing/stale fields, instrument IDs, timezone/currency and reconciliation.
3. Integration: import → validate → calculate → persist evidence → report, including retries and duplicate jobs.
4. Research: chronological evaluation, corporate actions and total-return benchmarks; costs and delays.
5. Security: authorization, tenant isolation, export/deletion, secret handling, malicious files, prompt injection and dependency review.
6. Acceptance: founder runs representative tasks and signs off evidence; no fictional approvals.

Current tests cover R01–R03 and the synthetic normalized reconciliation portion of R04. A passing suite does not establish Fidelity compatibility, complete broker-account reconciliation, production security, investment edge or commercial readiness. Remote CI results must be checked separately from local results.

## Backtesting protocol

Register the hypothesis, universe and benchmark before experimenting. Use information available at each decision date: filings after publication, macro vintage/revisions, historical constituents including delistings. Fit normalization on training data only. Use chronological walk-forward validation; purge/embargo overlapping label windows. Keep a final holdout untouched until model selection ends. Record every experiment, including failed ones, to expose selection bias.

Signals at a bar close execute no earlier than the next eligible tradable event. Account for bid/ask, slippage, commissions, dividends, splits, cash return, borrow/financing when applicable, trading halts and liquidity/capacity. Test fees and delays at adverse levels. Options history must include actual contract quotes and corporate-action adjustments; do not reconstruct tradable historical premiums from today's IV or a theoretical model and call them observed fills.

Compare aligned total returns with an agreed broad-equity benchmark and a risk-appropriate comparator. Candidate equity references include S&P 500 total return and a growth comparator, subject to data rights. For option income, also compare with owning the underlying and cash. Track CAGR, annualized volatility, Sharpe with matched risk-free series, Sortino, maximum drawdown, recovery time, turnover, exposure, tail losses, benchmark-relative return and confidence intervals. Distinguish time-weighted strategy performance from customer money-weighted returns. Annualization and statistical confidence need adequate history; return unavailable when unsupported.

Alpha claims require net-of-cost out-of-sample evidence, multiple-testing controls, regime robustness, capacity analysis and independent review. Success in one favorable period or high classification accuracy is insufficient. Do not use a short paper track record as a claim of market-beating reliability.

## Options boundaries

Current engine models standard 100-share USD contracts at expiration. CSP reserves gross strike obligation plus supplied fees without relying on unsettled premium. Covered calls require caller-supplied unencumbered shares; the engine cannot independently verify them. Fees are total user assumptions. It excludes early assignment, dividends, taxes, interest, spreads, time value, broker margin, adjusted contracts and share encumbrances across multiple strategies. The maximum-P&L number can be negative for an unfavorable covered-call entry. Breakeven is an algebraic reference and may be unreachable if above the call strike.

Future options gate: current chain with known timestamp; contract identity; position and available-cash reconciliation; exchange calendar; earnings/ex-dividend calendar; aggregate reservations; assignment scenario; limit policy; bid-based sale and conservative exit assumptions. Unknown inputs block actionable ranking. No naked shorts, margin lending or order execution in prototype.

## Definition of done

Requirement and issue linked; code reviewed; relevant tests pass; invalid-path tests added for financial logic; docs match behavior; actual evidence recorded; no personal data/secrets in diff; migration/rollback considered; PR ready for founder acceptance. Do not add meaningless tests or empty commits to create activity. Freeze nonessential features after November 28.
