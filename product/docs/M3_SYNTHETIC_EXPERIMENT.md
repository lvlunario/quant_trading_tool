# M3 synthetic experiment specification v1

Recorded October 15, 2026, before generating returns or inspecting results.
R09/R15, QNT-01, GitHub issue #4. Engineering specification under delegated
synthetic-development authority; no founder acceptance or investment conclusion.

## Question and fixed scope

Can a deterministic long/cash baseline be evaluated without future information,
with the same calendar and costs as its comparator? This is an engineering
hypothesis, not a claim of predictive edge. Use one invented USD instrument
`DEMO`, 200 ordered synthetic sessions (0–199), no leverage, shorts or options.
Prices, distributions and corporate actions will be invented and labeled as
such. Real watchlist names, personal holdings and licensed feeds are excluded.

Before running, freeze the generator version/seed, exact input checksum, code
commit and configuration checksum in an experiment record. The generator and
checked-in preregistration manifest and validation-only composition receipt are
now implemented; validated metrics and durable result persistence are not.
Retain failed runs and amendments; do not silently change this specification
after results.

## Evaluation protocol

- Candidate: long when trailing 20-session total return is positive; otherwise
  cash. No optimized threshold, learned model or hyperparameter search.
- Comparator: buy-and-hold the same invented instrument over the exact same
  eligible evaluation sessions; cash is a secondary comparator.
- Signal at session close; execution no earlier than next session's opening
  event. Missing events or unavailable signal inputs block the observation;
  never backfill from later data. Five-session forward labels are used only to
  exercise split isolation, not to create signals.
- Expanding folds: training starts at 0; validation intervals are [80,120) and
  [120,160). Final holdout [160,200) remains excluded from model selection.
- Label end is inclusive. A training label must end strictly before validation
  start minus a one-session safety gap. A validation label must end strictly
  before validation end. The planner purges labels touching either boundary.
- Any future fitted preprocessing must fit only on returned training sessions.
  Earlier validation may become later training once its labels have matured;
  the final holdout must never do so. Session metadata alone cannot enforce
  feature construction or prove that an analyst has not inspected holdout values.
- Base cost assumption: 10 basis points of traded notional per side, including
  all modeled commission/spread/slippage. Adverse case: 25 basis points per side
  plus one additional execution-session delay. These are invented test inputs,
  not empirical cost estimates. Apply the same assumptions to the comparator.
- Cash return, financing, borrow and taxes: zero in this limited synthetic case;
  the no-borrow/no-leverage constraints still apply. Corporate-action handling,
  capacity, tradability and observed market-cost calibration remain future work.
- Report gross/net cumulative return, maximum drawdown, turnover and exposure
  only after implementing independently checked accounting. No annualized
  statistics, confidence interval, alpha claim or performance number exists yet.
- Freeze selection before a separate final-holdout evaluation; do not repeatedly
  retune on holdout. A synthetic demonstration cannot establish real-world edge.

## Implemented slices and demos

`atlas.evaluation.plan_fold` accepts immutable session metadata and a `FoldSpec`.
It returns training, validation, purged and excluded decision-session tuples.
It rejects future feature availability, non-chronological or duplicate sessions,
invalid windows, validation crossing into holdout and empty usable partitions.
It performs no fitting, data retrieval, trade simulation, file I/O or release.
One sample per decision session is supported; panel/multi-instrument data is not.

From `product/`, run:

```sh
python -m unittest discover -s tests -p test_evaluation.py -v
```

The registered 200-session metadata case yields 74 training and 35 validation
samples in fold one, 114 training and 35 validation samples in fold two; every
holdout decision stays excluded. These are sample counts, not investment results.
The one-session gap is a conservative pre-validation separation, not a general
bidirectional cross-validation embargo implementation. An exchange-calendar
adapter is still required before these indices can represent actual sessions.

`atlas.synthetic_execution.run_long_cash_ledger` adds an exact Decimal,
synthetic-only next-event ledger. It accepts ordered invented open/close bars,
precomputed long/cash targets, initial cash and a fixed per-side cost/delay
policy. Long entry allocates available cash across notional and entry cost;
cash targets liquidate all synthetic shares and deduct exit cost. Repeated
targets do not trade. Missing decision/execution events, overlapping pending
decisions, invalid prices or ordering fail closed rather than shifting fills.

The independently calculated base fixture begins with $1,001, buys 100 invented
shares at $10 after 10 bps entry cost, then sells at $12 after 10 bps exit cost,
ending with $1,198.80. The adverse accounting fixture begins with $110.275,
uses a two-session delay and 25 bps per side, buys 10 shares at $11 and exits
at $9 for $89.775. These arithmetic cases verify bookkeeping and delay effects;
they are not observed returns or evidence for the registered strategy.

```sh
python -m unittest discover -s tests -p test_synthetic_execution.py -v
```

The ledger now preserves overlap rejection as the default and offers an explicit
FIFO alternative. FIFO queues each target for its original fixed-delay event;
later decisions do not cancel or move earlier targets, and a repeated target is
evaluated against exposure when its event executes. Independently worked tests
cover overlapping 25-bps/two-session entry and exit plus a repeated queued
target. The original base receipt continues to record the then-undefined
adverse policy; the October 21 amendment below separately selects FIFO. This
primitive does not generate signals, run
folds, model dividends/corporate actions, persist results or calculate metrics.

`atlas.synthetic_series` now implements the registered generator and signal as
a separate, unexecuted slice. Version `atlas.synthetic_series@1.0.0`, integer
seed `20261015` and a fixed integer linear-congruential state produce exactly
200 four-decimal invented open/close bars. The preregistered 20-session rule
emits only long/cash state changes through session 159; sessions 160–199 are
present but cannot produce model-selection targets. The registered fixture has
11 pre-holdout transitions. These counts and prices are generator regression
facts, not strategy performance.

```sh
python -m unittest discover -s tests -p test_synthetic_series.py -v
```

The generator and signal are now composed with the base and adverse ledgers only
for the two validation windows described below. No holdout return, comparator,
cost-adjusted metric or investment conclusion has been calculated or inspected.

`atlas.experiment_registry` canonicalizes the fixed configuration and complete
invented bar/target series, reproduces both bars and targets from the declared
seed, and binds their SHA-256 digests to an exact 40-character Git commit. The
checked-in [`fixtures/m3-experiment-manifest.json`](../fixtures/m3-experiment-manifest.json)
is `preregistered` against code commit `dd670ae`; its output hash is null,
holdout inspected is false and investment performance established is false.
A separate receipt can later hash opaque synthetic output bytes, but cannot
promote those bytes to validated performance or assert holdout inspection.

```sh
python -m unittest discover -s tests -p test_experiment_registry.py -v
```

`atlas.validation_run` composes the exact manifest, registered series, fixed
folds and base execution ledger. It creates one target at each validation start
from information available at that close, then includes only eligible target
changes. Fold one records 74 training, 35 validation, 11 purged and 80 excluded
samples with five targets/fills; fold two records 114/35/11/40 with two
targets/fills. Bars at and after session 160 never enter either ledger.

[`fixtures/m3-validation-manifest.json`](../fixtures/m3-validation-manifest.json)
binds the amendment to exact feature commit `b7cf135`; the paired
[`fixtures/m3-validation-receipt.json`](../fixtures/m3-validation-receipt.json)
binds 460 canonical structural bytes. It deliberately excludes cash, shares,
marked values and every performance metric. Comparator and adverse policies are
not executed. The adverse case remains blocked because daily targets can
overlap the two-session delay and the current ledger correctly refuses to infer
event-netting semantics.

The October 21 adverse amendment appends
`adverse_overlap_policy=fifo` to the otherwise unchanged canonical
configuration and binds it to feature commit `bca940e`. The paired
[`m3-adverse-validation-manifest.json`](../fixtures/m3-adverse-validation-manifest.json)
and
[`m3-adverse-validation-receipt.json`](../fixtures/m3-adverse-validation-receipt.json)
run the same two validation folds at 25 bps per side and a two-session delay.
They record five and two targets/fills, respectively, and bind 409 canonical
structural bytes. Cash, shares, marked values, returns and every metric remain
excluded; comparator execution and holdout inspection are false.

The October 22 comparator amendment uses the same FIFO-amended configuration
and exact invented input hash. Its checked-in
[`m3-comparator-validation-manifest.json`](../fixtures/m3-comparator-validation-manifest.json)
binds feature commit `40ce171`, and the paired
[`m3-comparator-validation-receipt.json`](../fixtures/m3-comparator-validation-receipt.json)
runs one buy-and-hold target in each [80,120) and [120,160) calendar under both
10-bps/one-session and 25-bps/two-session-FIFO assumptions. Each fold retains
35 eligible decision samples, marks only at sessions 119 and 159, and records
one target/fill per policy. The 483 canonical bytes contain no cash, shares,
marked values, returns, drawdowns, turnover or exposure. Metrics and holdout
inspection remain false.

```sh
python -m unittest discover -s tests -p test_validation_run.py -v
```

## Next increment and acceptance boundary

Define independently checked validation-only cumulative-return, drawdown,
turnover and exposure arithmetic before emitting any candidate/comparator
metric. Keep the final holdout sealed until model selection freezes.
M3 target remains October 31. M2 sourced-workbench deferrals remain independent;
this work grants no data rights, Fidelity compatibility, release permission or
founder approval.
