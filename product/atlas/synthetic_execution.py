"""Deterministic long/cash execution accounting for invented session data.

This module is deliberately narrower than a backtester.  It processes ordered
synthetic bars and precomputed target states, applies a fixed next-event delay
and records exact Decimal costs.  It does not create signals, fetch data,
annualize results or make an investment claim.
"""
from dataclasses import dataclass
from decimal import Decimal


ZERO = Decimal('0')
ONE = Decimal('1')
TEN_THOUSAND = Decimal('10000')


def _session(value: int) -> bool:
    return type(value) is int and value >= 0


def _finite_positive(value: Decimal) -> bool:
    return isinstance(value, Decimal) and value.is_finite() and value > ZERO


@dataclass(frozen=True)
class SyntheticBar:
    session: int
    open_price: Decimal
    close_price: Decimal

    def __post_init__(self):
        if not _session(self.session):
            raise ValueError('invalid_bar_session')
        if not all(_finite_positive(value) for value in
                   (self.open_price, self.close_price)):
            raise ValueError('invalid_bar_price')


@dataclass(frozen=True)
class TargetState:
    decision_session: int
    target_exposure: Decimal

    def __post_init__(self):
        if not _session(self.decision_session):
            raise ValueError('invalid_decision_session')
        if (not isinstance(self.target_exposure, Decimal) or
                self.target_exposure not in (ZERO, ONE)):
            raise ValueError('unsupported_target_exposure')


@dataclass(frozen=True)
class ExecutionPolicy:
    cost_bps_per_side: int
    delay_sessions: int = 1

    def __post_init__(self):
        if (type(self.cost_bps_per_side) is not int or
                not 0 <= self.cost_bps_per_side <= 10000):
            raise ValueError('invalid_cost_bps')
        if type(self.delay_sessions) is not int or self.delay_sessions < 1:
            raise ValueError('invalid_execution_delay')

    @property
    def cost_rate(self) -> Decimal:
        return Decimal(self.cost_bps_per_side) / TEN_THOUSAND


@dataclass(frozen=True)
class ExecutionFill:
    decision_session: int
    execution_session: int
    from_exposure: Decimal
    to_exposure: Decimal
    execution_price: Decimal
    quantity: Decimal
    traded_notional: Decimal
    transaction_cost: Decimal
    cash_after: Decimal
    shares_after: Decimal


@dataclass(frozen=True)
class ExecutionLedger:
    initial_cash: Decimal
    policy: ExecutionPolicy
    fills: tuple[ExecutionFill, ...]
    ending_cash: Decimal
    ending_shares: Decimal
    marked_at_session: int
    ending_marked_value: Decimal
    synthetic_only: bool = True
    investment_performance_established: bool = False


def run_long_cash_ledger(
        bars: tuple[SyntheticBar, ...], signals: tuple[TargetState, ...],
        *, initial_cash: Decimal, policy: ExecutionPolicy) -> ExecutionLedger:
    """Execute target changes after an exact ordered-session delay.

    A long entry invests all cash including entry cost; a cash target sells all
    shares and deducts exit cost. Repeated targets create no trade. Missing
    execution events, overlapping pending decisions and post-data decisions
    fail closed rather than being shifted or backfilled.
    """
    if not isinstance(bars, tuple) or not bars or any(
            not isinstance(row, SyntheticBar) for row in bars):
        raise ValueError('invalid_synthetic_bars')
    if not isinstance(signals, tuple) or not signals or any(
            not isinstance(row, TargetState) for row in signals):
        raise ValueError('invalid_target_states')
    if not _finite_positive(initial_cash) or not isinstance(policy, ExecutionPolicy):
        raise ValueError('invalid_ledger_input')

    sessions = tuple(row.session for row in bars)
    if sessions != tuple(sorted(set(sessions))):
        raise ValueError('bars_must_be_unique_and_chronological')
    decisions = tuple(row.decision_session for row in signals)
    if decisions != tuple(sorted(set(decisions))):
        raise ValueError('signals_must_be_unique_and_chronological')

    bar_index = {row.session: index for index, row in enumerate(bars)}
    scheduled: list[tuple[TargetState, SyntheticBar]] = []
    execution_indices: list[int] = []
    for signal in signals:
        if signal.decision_session not in bar_index:
            raise ValueError('missing_decision_event')
        decision_index = bar_index[signal.decision_session]
        execution_index = decision_index + policy.delay_sessions
        if execution_index >= len(bars):
            raise ValueError('missing_execution_event')
        if (execution_indices and
                (execution_index <= execution_indices[-1] or
                 decision_index < execution_indices[-1])):
            raise ValueError('overlapping_execution_event')
        execution_indices.append(execution_index)
        scheduled.append((signal, bars[execution_index]))

    cash, shares, exposure = initial_cash, ZERO, ZERO
    fills: list[ExecutionFill] = []
    for signal, bar in scheduled:
        if signal.target_exposure == exposure:
            continue
        price, rate = bar.open_price, policy.cost_rate
        if signal.target_exposure == ONE:
            notional = cash / (ONE + rate)
            cost = cash - notional
            quantity = notional / price
            cash = ZERO
            shares = quantity
        else:
            quantity = shares
            notional = quantity * price
            cost = notional * rate
            cash = cash + notional - cost
            shares = ZERO
        fills.append(ExecutionFill(
            signal.decision_session, bar.session, exposure,
            signal.target_exposure, price, quantity, notional, cost, cash, shares))
        exposure = signal.target_exposure

    last = bars[-1]
    marked_value = cash + shares * last.close_price
    return ExecutionLedger(
        initial_cash, policy, tuple(fills), cash, shares, last.session,
        marked_value)
