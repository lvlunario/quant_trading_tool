"""Registered invented session series and fixed trailing-return signal.

The generator is deterministic test infrastructure.  Its bars are not market
data and its targets are not recommendations or evidence of investment edge.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

from .synthetic_execution import SyntheticBar, TargetState


GENERATOR_VERSION = 'atlas.synthetic_series@1.0.0'
REGISTERED_SEED = 20261015
REGISTERED_SESSIONS = 200
REGISTERED_LOOKBACK = 20
_MODULUS = 2 ** 32
_PRICE_QUANTUM = Decimal('0.0001')
_BPS = Decimal('10000')


@dataclass(frozen=True)
class SyntheticSeries:
    generator_version: str
    seed: int
    bars: tuple[SyntheticBar, ...]
    targets: tuple[TargetState, ...]
    lookback_sessions: int
    synthetic_only: bool = True
    holdout_inspected: bool = False
    investment_performance_established: bool = False


def _next_state(state: int) -> int:
    return (1664525 * state + 1013904223) % _MODULUS


def generate_bars(*, seed: int, sessions: int) -> tuple[SyntheticBar, ...]:
    """Create positive invented OHLC subsets from an integer LCG state."""
    if type(seed) is not int or not 0 < seed < _MODULUS:
        raise ValueError('invalid_synthetic_seed')
    if type(sessions) is not int or not 2 <= sessions <= 10000:
        raise ValueError('invalid_synthetic_session_count')
    state, previous_close = seed, Decimal('100.0000')
    rows: list[SyntheticBar] = []
    for session in range(sessions):
        state = _next_state(state)
        gap_bps = Decimal(state % 21 - 10)
        state = _next_state(state)
        intraday_bps = Decimal(state % 101 - 50)
        open_price = (previous_close * (Decimal('1') + gap_bps / _BPS)).quantize(
            _PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)
        close_price = (open_price * (Decimal('1') + intraday_bps / _BPS)).quantize(
            _PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)
        rows.append(SyntheticBar(session, open_price, close_price))
        previous_close = close_price
    return tuple(rows)


def trailing_target_changes(
        bars: tuple[SyntheticBar, ...], *, lookback_sessions: int,
        holdout_start: int) -> tuple[TargetState, ...]:
    """Return only long/cash state changes before the reserved holdout.

    The decision at session t compares only closes at t and t-lookback.  The
    current close is available at the decision, so execution must occur later.
    Holdout bars may be present for later evaluation but cannot create targets
    in this model-selection series.
    """
    if not isinstance(bars, tuple) or not bars or any(
            not isinstance(row, SyntheticBar) for row in bars):
        raise ValueError('invalid_signal_bars')
    sessions = tuple(row.session for row in bars)
    if sessions != tuple(range(len(bars))):
        raise ValueError('signal_bars_must_be_contiguous')
    if (type(lookback_sessions) is not int or lookback_sessions < 1 or
            lookback_sessions >= len(bars)):
        raise ValueError('invalid_signal_lookback')
    if (type(holdout_start) is not int or
            not lookback_sessions < holdout_start < len(bars)):
        raise ValueError('invalid_signal_holdout')

    targets: list[TargetState] = []
    previous_target: Decimal | None = None
    for session in range(lookback_sessions, holdout_start):
        target = (Decimal('1') if bars[session].close_price >
                  bars[session - lookback_sessions].close_price else Decimal('0'))
        if target != previous_target:
            targets.append(TargetState(session, target))
            previous_target = target
    if not targets:
        raise ValueError('no_registered_targets')
    return tuple(targets)


def registered_series() -> SyntheticSeries:
    bars = generate_bars(seed=REGISTERED_SEED, sessions=REGISTERED_SESSIONS)
    targets = trailing_target_changes(
        bars, lookback_sessions=REGISTERED_LOOKBACK, holdout_start=160)
    return SyntheticSeries(
        GENERATOR_VERSION, REGISTERED_SEED, bars, targets,
        REGISTERED_LOOKBACK)
