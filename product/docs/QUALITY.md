# Research, QA and release quality

## Verification levels

1. Unit: independent expected values for money, weights and expiry payoffs; invalid-input cases.
2. Contract: provider schemas, missing/stale fields, instrument IDs, timezone/currency and reconciliation.
3. Integration: import → validate → calculate → persist evidence → report, including retries and duplicate jobs.
4. Research: chronological evaluation, corporate actions and total-return benchmarks; costs and delays.
5. Security: authorization, tenant isolation, export/deletion, secret handling, malicious files, prompt injection and dependency review.
6. Acceptance: founder runs representative tasks and signs off evidence; no fictional approvals.

Current tests cover R01–R03, the synthetic broker-shaped mapping and normalized reconciliation portions of R04, contract-level missing/ambiguous/effective-date/rights decisions for R06, source-bound metric readiness for R07, macro release/vintage selection for R08, historical revision selection for R15, and the combined research-input gate. Source-intake tests cover exact-byte hashing, permission precedence, content/size bounds, encoding/PDF-header checks, safe metadata failures and non-retention of content. Source-catalog and review tests require an exact dated universe, identity/document agreement, a blocked unreviewed state and an immutable safe retrieval policy; premature rights promotion, unknown fields, future assessments or network enablement fail. Worksheet tests require exact eight-source ordering, public source bindings, the complete pending checklist and exact blank evidence contract; missing or promoted review tasks fail. Its public readiness test requires eight pending tasks, 64 pending per-source checks, zero completions and no source/review evidence fields. Reviewed-rights tests require the complete manual checklist, exact terms/document/reviewer bindings, valid timing and action scope; they distinguish missing, conflicting, expired, prohibited, counsel-required and permitted decisions while preserving separate retrieval/release gates. The fixed source-workflow tests cover permission-before-extraction, exact fixture hashing, full metric release, missing-value blocking, changed-byte provenance and strict JSON/schema rejection; its subprocess test checks that raw source fields remain absent. Extraction-quality tests require exact document/source/metric/payload bindings, deterministic or human-verified release evidence, valid timing, and blocked unverified/rejected states. Extractor-conformance tests enforce nominal/missing/schema/identity/unit/period coverage, zero false accepts/rejects/mismatches, strict manifest identity and redacted reporting. Provider-qualification tests require exact provider/dataset/extractor identity, current private authorization, representative sample size, independent review, full declared-format coverage, minimum exact-match quality and zero critical/semantic errors; synthetic-only or absent evidence remains blocked and public reports omit private identifiers. Source-binding tests require exact instrument/provider/dataset, URI, digest and availability agreement, and reject future or temporally impossible retrievals. Macro tests prove that revisions unavailable at a decision time cannot leak backward, and that missing values remain missing rather than zero. Mapping tests require every source row to survive as a recognized, unsupported or invalid outcome; they cover alternate profile-driven headers/types, exact delimited headers, total footers, malformed/data-after-footer records, encoding/size limits, invalid profile semantics, duplicate cash, total mismatch, stale sources and strict schema rejection. A passing suite does not authenticate a publisher, establish Fidelity compatibility, populate a security master or macro feed, qualify a real extractor without its private evidence, prove provider permission or source accuracy, complete broker-account reconciliation, demonstrate production security, investment edge or commercial readiness. Remote CI results must be checked separately from local results.

Weekly-report tests require the exact four-section order, one shared cutoff date,
unique synthetic statement IDs and the evidence/source state permitted for each
claim type. They reject future periods, naive generation times, missing,
duplicate or reordered sections and attempts to promote assumptions into
verified observations. The CLI/privacy check excludes real watchlist symbols,
metric values and recommendation fields.
Weekly Review HTTP tests require that same order and evidence semantics on one
exact allowlisted route, no-store response handling, false
conclusion/acceptance/release flags and exclusion of real watchlist symbols,
evidence identifiers and all form/action controls. Query-driven report dates
are rejected rather than interpreted.
Weekly-readiness tests require one shared cutoff across the report and M2 trace,
the exact four-section synthetic shell, the current six-stage public counts,
zero sourced statements/metrics and false conclusion/acceptance/release flags.
Mismatched times, wrong input types and unsupported nonzero sourced extraction
or metric counts fail closed; CLI and UI summaries exclude evidence identifiers.
Source-completeness tests lock the four-rule order, exact evidence requirement
and required-field set for each claim type. They reject omitted or reordered
rules, altered field contracts, naive timestamps and any permission for an
unbound factual claim. The CLI check requires zero complete claims, statements
and metrics, blocked eligibility and no issuer, evidence value or metric data.
Claim-receipt tests lock the fixed 23/13/10 required/provided/missing totals,
per-section counts and false actual-report/release flags. Unknown, duplicate or
reordered field declarations, section reordering, naive cutoffs and non-binding
objects fail closed. CLI/privacy coverage requires counts only and excludes
field names, evidence identifiers and values. These tests prove structural
accounting, not evidence permission, accuracy or completeness.
The Weekly Review receipt-projection test requires the same aggregate and
per-section counts, one synthetic field-complete section, three blocked
sections, zero actual complete claims and false report eligibility. It rejects
the underlying field names and evidence identifiers from rendered HTML.
Weekly-publication tests require aligned assessment times, monotonic six-stage
counts, exact claim arithmetic, zero sourced statements/metrics and a blocked
decision. They separately prove that marking all 23 synthetic fields present
still cannot create actual eligibility or release authority. CLI/privacy checks
exclude field names, evidence identifiers, source addresses, hashes and values.
The Weekly Review decision-projection test requires `withhold_publication`, the
23/13/10 binding counts, zero sourced statements/metrics and false eligibility
and release flags while excluding evidence identifiers, addresses, hashes and
metric values from HTML.
M2 milestone-readiness tests require aligned assessment times, a passing 6/6
invented conformance path, unchanged public 8/8/0/0/0/0 counts, the blocked
weekly publication decision and false acceptance/release flags. Time drift,
weakened synthetic proof, changed public counts and invalid target/count
arithmetic fail closed; CLI output excludes private evidence fields.
The Weekly Review milestone-projection test locks the blocked October 17 state,
6/6 invented technical gates, 0/6 sourced exit criteria, five external
dependencies and false acceptance/release flags. It also rejects dependency
codes and evidence-bearing identifiers from rendered HTML.
The criterion-detail projection test requires the exact identity, discovery,
rights, capture, extraction and metric-release order; exact 8/9, 8/9, 0/8,
0/8, 0/9 and 0/9 counts; blocked status; and controlled blocker labels.
M2 disposition tests require every unresolved criterion to become an explicit
deferral, completed criteria to become review recommendations rather than
acceptance, the checkpoint state to derive from the assessment date and all
founder-response/acceptance/release flags to remain false. Invalid inputs and a
weakened publication decision fail closed; CLI output excludes evidence and
approval identifiers.
Synthetic-series tests lock the generator version, seed, 200-session output and
all 11 pre-holdout target transitions. They independently exercise the
20-session comparison, prove that holdout sessions cannot emit selection
targets and reject invalid seeds, sizes, ordering, lookbacks and holdout bounds.
They do not test strategy returns, market realism or investment validity.
Experiment-registry tests independently specify canonical series bytes, require
reproduction of bars and targets from the seed, bind an exact code commit and
prove configuration/input/output byte changes alter their digests. The
checked-in manifest is regenerated in test and must remain preregistered with a
null output hash. Invalid identifiers, empty output and any attempted holdout or
performance promotion fail closed. Hash agreement proves identity, not meaning.
Validation-composition tests lock both registered fold partitions, five and two
base-policy target/fill events, the exact canonical structural bytes and their
output digest. They reject manifest/config drift and any receipt that promotes
comparator, adverse, metric, holdout or performance state. The receipt excludes
cash, shares, marked values, returns, drawdown, turnover and exposure. These
checks establish composition and identity only; independent metric arithmetic,
benchmark/adverse execution and final-holdout evidence remain pending.
The Weekly Review projection test requires four count-only rows, exact 8/5/5/5
required-field counts, zero complete claims, missing evidence values and false
report eligibility while excluding every underlying field name. The October 10
research-packet tests require the full watchlist plus AVGO, an explicit CRBS
identity block, separated observations/hypotheses/missing data and the
point-in-time, holdout, benchmark, cost and premium-income boundaries.

Source-capture authorization tests enforce the independent two-key rule,
exact catalog-document binding, current approval time, safe size/content limits,
no redirects or byte retention, zero release authority and redacted public
receipts. They exercise permitted rights without technical approval, current,
expired and future approvals, unsafe policy rejection and the fully blocked
checked-in CLI state. These tests validate the gate contract, not a downloader,
private approval process or source permission.

M2 acceptance-trace tests lock the gate order, current 8/8/0/0/0/0 pass counts,
monotonic progression, input alignment, blocked acceptance/release flags and
the absence of evidence-bearing or financial fields from CLI output.
The workbench trace test also checks all four fixed routes, exact six-stage
ordering/counts, false milestone/release flags and the same privacy exclusions.
Synthetic M2 conformance tests separately require the invented fixture to pass
all six technical gates, require an exact current capture approval before byte
intake, require public extraction and release to stay at zero, block when the
invented workflow cannot release a metric, and assert that
identifiers, hashes and metric values are absent from the summary. Passing this
scenario proves contract composition, not public-source permission, provider
accuracy or investment performance.
The workbench projection test repeats the contract across all four fixed routes,
locks the synthetic 6/6 and public 8/8/0/0/0/0 states, and rejects identifiers,
hashes and the invented metric value from rendered HTML.

Research-work-item tests require the exact nine-name universe, aligned registry,
catalog and rights assessment times, controlled blocker/action codes and release
false. They prove that rights permission alone advances only to missing source
evidence and that public output omits source/review evidence and financial fields.
Workbench HTTP tests require all nine rows on the default route, exact 1/0/8
identity/source/rights subsets on fixed routes, a count-only blank-worksheet
projection, a count-only two-key capture projection, no form or evidence
identifiers, and rejection of query-driven or
arbitrary filters. These are structural and
privacy controls; they do not establish browser usability or accessibility.

UX-01 preview tests require its displayed portfolio and option values to equal a fixed model calculated by the deterministic risk kernel. Its synthetic research trace must equal the metric payload admitted by the combined point-in-time, identity, rights and evidence-binding gate. The reviewed-rights projection must equal the backend empty-register decision, show all eight candidates blocked and omit terms/reviewer evidence fields. The provider-qualification projection must equal the backend no-evidence decision and must omit private evidence fields. Tests also check document structure and offline boundaries. These checks prevent mockup/model drift; they do not verify browser rendering, accessibility, usability or current data.

The local interactive Options Lab has HTTP integration tests for the full GET → tokenized POST → kernel-result path plus invalid token, collateral, field multiplicity, path and request-size cases. A manual localhost smoke test repeats the default request. These do not replace cross-browser, responsive, keyboard or accessibility testing.

The synthetic broker demo has a subprocess-level check that its JSON result reconciles, retains one mapped outcome per input row, states that it is not Fidelity-validated and does not echo the invented position symbol. The synthetic CSV command is checked against the exact fixture digest, a blocked malformed-row path and a two-attempt private-ledger workflow that suppresses publication on the second attempt. Tests assert that position fields, raw marker content and private paths are absent from output. This verifies CLI wiring and safe summary behavior, not a real broker format.

## Backtesting protocol

The M3 split tests verify exact hand-calculated partitions, inclusive boundary
purging, label-maturity safety gaps, future-feature rejection, invalid windows,
unique chronological sessions, empty-partition failure and two expanding folds
that exclude every final-holdout sample. These checks do not establish feature
provenance, preprocessing discipline, market returns or a working backtester.
See [the registered synthetic protocol](M3_SYNTHETIC_EXPERIMENT.md).
The synthetic execution tests independently check entry/exit notional, costs,
cash and shares under the registered base and adverse policies. They also check
repeated-target no-ops and reject missing events, non-Decimal/invalid prices,
invalid policies, duplicate/unsorted inputs and overlapping delayed decisions
under the default. Separate hand-calculated cases prove that explicit FIFO
executes two overlapping 25-bps/two-session targets at their fixed events and
treats a repeated queued target as a no-op at execution. These tests prove
bounded accounting behavior, not fill realism, a complete event engine,
investable performance or production order handling.

The adverse-validation registration tests independently prove that FIFO changes
the configuration hash without changing the original preregistration bytes,
that the exact manifest reproduces both validation folds under 25 bps and a
two-session delay, and that mismatched manifests or attempted metric/holdout
promotion fail closed. The checked-in adverse receipt contains structural
counts only; it is not a performance result.

The M3 metric-arithmetic tests use independent small invented ledgers to verify
gross replay, cost-inclusive net return, initial-capital/running-peak drawdown,
absolute-notional turnover and close-mark exposure. They include a round trip,
a 25% peak-to-trough loss, entry-cost drawdown, FIFO/delay preservation and
fail-closed missing events. These tests fix arithmetic semantics only: the
kernel is not connected to the registered experiment, releases no candidate or
comparator result and cannot promote holdout or investment-performance state.

The registered validation-metric tests require both exact fold calendars, 40
close marks per candidate/comparator/policy vector, exact manifest and output
hashes, and rejection of changed configuration, identity or state. The public
fixture serializes Decimal metrics as strings and excludes every price, cash,
share, quantity, fill and traded-notional field. Passing these tests does not
freeze selection, validate real data or authorize final-holdout inspection.

Register the hypothesis, universe and benchmark before experimenting. Use information available at each decision date: filings after publication, macro vintage/revisions, historical constituents including delistings. Fit normalization on training data only. Use chronological walk-forward validation; purge/embargo overlapping label windows. Keep a final holdout untouched until model selection ends. Record every experiment, including failed ones, to expose selection bias.

Signals at a bar close execute no earlier than the next eligible tradable event. Account for bid/ask, slippage, commissions, dividends, splits, cash return, borrow/financing when applicable, trading halts and liquidity/capacity. Test fees and delays at adverse levels. Options history must include actual contract quotes and corporate-action adjustments; do not reconstruct tradable historical premiums from today's IV or a theoretical model and call them observed fills.

Compare aligned total returns with an agreed broad-equity benchmark and a risk-appropriate comparator. Candidate equity references include S&P 500 total return and a growth comparator, subject to data rights. For option income, also compare with owning the underlying and cash. Track CAGR, annualized volatility, Sharpe with matched risk-free series, Sortino, maximum drawdown, recovery time, turnover, exposure, tail losses, benchmark-relative return and confidence intervals. Distinguish time-weighted strategy performance from customer money-weighted returns. Annualization and statistical confidence need adequate history; return unavailable when unsupported.

Alpha claims require net-of-cost out-of-sample evidence, multiple-testing controls, regime robustness, capacity analysis and independent review. Success in one favorable period or high classification accuracy is insufficient. Do not use a short paper track record as a claim of market-beating reliability.

## Options boundaries

Current engine models standard 100-share USD contracts at expiration. CSP reserves gross strike obligation plus supplied fees without relying on unsettled premium. Covered calls require caller-supplied unencumbered shares; the engine cannot independently verify them. Fees are total user assumptions. It excludes early assignment, dividends, taxes, interest, spreads, time value, broker margin, adjusted contracts and share encumbrances across multiple strategies. The maximum-P&L number can be negative for an unfavorable covered-call entry. Breakeven is an algebraic reference and may be unreachable if above the call strike.

Future options gate: current chain with known timestamp; contract identity; position and available-cash reconciliation; exchange calendar; earnings/ex-dividend calendar; aggregate reservations; assignment scenario; limit policy; bid-based sale and conservative exit assumptions. Unknown inputs block actionable ranking. No naked shorts, margin lending or order execution in prototype.

## Definition of done

Requirement and issue linked; code reviewed; relevant tests pass; invalid-path tests added for financial logic; docs match behavior; actual evidence recorded; no personal data/secrets in diff; migration/rollback considered; PR ready for founder acceptance. Do not add meaningless tests or empty commits to create activity. Freeze nonessential features after November 28.

Import receipt tests verify the exact field allowlist, duplicate/unchecked decisions, blocked-state precedence and rejection of contradictory publication counts. Receipts summarize engine results and do not independently verify source authenticity or financial correctness.
