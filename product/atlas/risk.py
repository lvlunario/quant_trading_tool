"""Deterministic USD, long-only snapshot and standard-option calculations.

All monetary values use Decimal. Results are educational calculations, not
recommendations, forecasts, tax calculations, or broker buying-power checks.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


def amount(value):
    if isinstance(value, (bool, float)):
        raise ValueError("Use decimal strings or integers, not floats/bools")
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid decimal value") from None
    if not number.is_finite() or number < 0:
        raise ValueError("Amount must be finite and nonnegative")
    return number


def snapshot_report(snapshot, *, now=None, max_age=timedelta(days=4)):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or max_age <= timedelta(0):
        raise ValueError("Aware clock and positive freshness limit required")
    if snapshot.get("schema_version") != 1 or snapshot.get("currency") != "USD":
        raise ValueError("Only schema 1, USD snapshots are supported")
    if snapshot.get("mode") not in ("synthetic", "user_export"):
        raise ValueError("Explicit synthetic or user_export mode required")
    try:
        timestamp = datetime.fromisoformat(snapshot["as_of"])
    except (ValueError, TypeError, KeyError):
        raise ValueError("ISO as_of timestamp required") from None
    if timestamp.tzinfo is None or timestamp > now or now-timestamp > max_age:
        raise ValueError("Timestamp is naive, future, or stale")
    cash = amount(snapshot["cash"])
    positions = snapshot["positions"]
    if not isinstance(positions, list):
        raise ValueError("positions must be a list")
    by_symbol = {}
    for position in positions:
        symbol = position["symbol"]
        if not isinstance(symbol, str) or not symbol or symbol != symbol.strip().upper():
            raise ValueError("Canonical uppercase symbol required")
        if position.get("asset_type") != "equity":
            raise ValueError("Only long equities; options must not be silently omitted")
        if symbol in by_symbol:
            raise ValueError("Duplicate symbol: aggregate reconciled lots before import")
        quantity, price = amount(position["quantity"]), amount(position["price"])
        if quantity == 0 or price == 0:
            raise ValueError("Positive quantity and price required")
        by_symbol[symbol] = quantity * price
    total = cash + sum(by_symbol.values(), Decimal(0))
    if total == 0:
        raise ValueError("Snapshot value must be positive")
    return {
        "schema_version": 1, "mode": snapshot["mode"], "as_of": timestamp.isoformat(),
        "currency": "USD", "total_value": str(total), "cash_weight": str(cash/total),
        "equity_weights": {symbol: str(value/total) for symbol, value in sorted(by_symbol.items())},
        "largest_equity_weight": str(max(by_symbol.values(), default=Decimal(0))/total),
        "readiness": "snapshot arithmetic only; not investment-ready",
        "limitations": ["No liabilities, options, taxes, FX, or suitability assessment",
                        "Prices supplied by caller; no independent quote verification"],
    }


def standard_option_payoff(*, strategy, contracts, strike, premium_per_share,
                           terminal_price, fees="0", shares=0, stock_entry=None,
                           available_cash="0", multiplier=100):
    """Expiry P&L for unadjusted USD equity contracts; premium is per share.

    Covered-call P&L covers only matched shares. No time value, dividends,
    early exercise, interest, taxes, or liquidation assumption is modeled.
    Fees are total entry/exit/assignment fees supplied by the caller.
    """
    if type(contracts) is not int or contracts < 1 or type(multiplier) is not int or multiplier != 100:
        raise ValueError("Positive integer contracts; only standard 100-share contracts")
    k, p, terminal, cost = map(amount, (strike, premium_per_share, terminal_price, fees))
    if k == 0 or p >= k:
        raise ValueError("Positive strike and premium below strike required")
    units = contracts * multiplier
    if strategy == "cash_secured_put":
        reserve = k * units + cost
        if amount(available_cash) < reserve:
            raise ValueError("Insufficient cash for gross strike obligation plus fees")
        pnl = (p - max(k-terminal, Decimal(0))) * units - cost
        maximum_loss = (k-p) * units + cost
        cap = p*units-cost
        breakeven = k-p+cost/units
    elif strategy == "covered_call":
        if amount(shares) < units:
            raise ValueError("Insufficient unencumbered shares")
        entry = amount(stock_entry)
        if entry == 0 or p >= entry:
            raise ValueError("Positive entry and premium below entry required")
        pnl = (min(terminal, k)-entry+p) * units-cost
        maximum_loss = (entry-p)*units+cost
        cap = (k-entry+p)*units-cost
        breakeven = entry-p+cost/units
        reserve = Decimal(0)
    else:
        raise ValueError("Unsupported strategy")
    return {"strategy": strategy, "contracts": contracts, "multiplier": multiplier,
            "expiration_pnl": str(pnl), "maximum_loss": str(maximum_loss),
            "maximum_pnl": str(cap), "breakeven": str(breakeven),
            "required_cash": str(reserve), "required_shares": units if strategy == "covered_call" else 0,
            "readiness": "hypothetical expiration calculation; not an order"}
