"""Exact validation metric arithmetic for synthetic long/cash ledgers.

This module defines the registered metric semantics on caller-supplied invented
bars and targets. It does not load an experiment manifest, select a strategy,
inspect a holdout, fetch market data or establish investment performance.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .synthetic_execution import (
    ExecutionLedger, ExecutionPolicy, SyntheticBar, TargetState,
    run_long_cash_ledger,
)


ZERO = Decimal('0')
ONE = Decimal('1')


def _finite(value: Decimal) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


@dataclass(frozen=True)
class EvaluationMetrics:
    gross_cumulative_return: Decimal
    net_cumulative_return: Decimal
    maximum_drawdown: Decimal
    turnover_on_initial_capital: Decimal
    long_exposure_fraction: Decimal
    marked_session_count: int
    synthetic_only: bool = True
    holdout_inspected: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        values = (
            self.gross_cumulative_return, self.net_cumulative_return,
            self.maximum_drawdown, self.turnover_on_initial_capital,
            self.long_exposure_fraction)
        if (any(not _finite(value) for value in values) or
                self.gross_cumulative_return < -ONE or
                self.net_cumulative_return < -ONE or
                not ZERO <= self.maximum_drawdown <= ONE or
                self.turnover_on_initial_capital < ZERO or
                not ZERO <= self.long_exposure_fraction <= ONE or
                type(self.marked_session_count) is not int or
                self.marked_session_count < 1 or
                self.synthetic_only is not True or
                self.holdout_inspected is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_evaluation_metrics')


def _marked_path(
        bars: tuple[SyntheticBar, ...], ledger: ExecutionLedger,
        initial_cash: Decimal) -> tuple[tuple[Decimal, ...], int]:
    fills = {fill.execution_session: fill for fill in ledger.fills}
    cash, shares = initial_cash, ZERO
    values: list[Decimal] = []
    long_sessions = 0
    for bar in bars:
        fill = fills.get(bar.session)
        if fill is not None:
            cash, shares = fill.cash_after, fill.shares_after
        if shares != ZERO:
            long_sessions += 1
        values.append(cash + shares * bar.close_price)
    return tuple(values), long_sessions


def _maximum_drawdown(
        marked_values: tuple[Decimal, ...], initial_cash: Decimal) -> Decimal:
    peak = initial_cash
    maximum = ZERO
    for value in marked_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        if drawdown > maximum:
            maximum = drawdown
    return maximum


def calculate_evaluation_metrics(
        bars: tuple[SyntheticBar, ...], signals: tuple[TargetState, ...], *,
        initial_cash: Decimal, policy: ExecutionPolicy) -> EvaluationMetrics:
    """Calculate fixed synthetic metrics without experiment selection.

    Gross return replays the identical signals, delay and overlap policy at zero
    transaction cost. Net return and drawdown include the supplied per-side
    cost. Turnover is absolute net traded notional divided by initial capital.
    Exposure is the fraction of supplied close marks held long after any opening
    fill at that session. The initial capital is included as the drawdown peak.
    """
    net = run_long_cash_ledger(
        bars, signals, initial_cash=initial_cash, policy=policy)
    gross = run_long_cash_ledger(
        bars, signals, initial_cash=initial_cash,
        policy=replace(policy, cost_bps_per_side=0))
    net_path, long_sessions = _marked_path(bars, net, initial_cash)
    return EvaluationMetrics(
        gross.ending_marked_value / initial_cash - ONE,
        net.ending_marked_value / initial_cash - ONE,
        _maximum_drawdown(net_path, initial_cash),
        sum((fill.traded_notional for fill in net.fills), ZERO) / initial_cash,
        Decimal(long_sessions) / Decimal(len(bars)),
        len(bars),
    )
