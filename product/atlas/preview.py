"""Synthetic, fixed UX-preview model derived from the deterministic risk kernel."""
from datetime import datetime, timezone
from decimal import Decimal

from .risk import snapshot_report, standard_option_payoff


PREVIEW_AS_OF = datetime(2026, 9, 12, tzinfo=timezone.utc)


def synthetic_preview_model():
    """Return the exact fixed values shown by the offline M0 preview.

    This is a regression contract, not a live quote, editable scenario, account
    snapshot, recommendation or promise that the HTML calls Python at runtime.
    """
    snapshot = {"schema_version": 1, "mode": "synthetic", "currency": "USD",
                "as_of": PREVIEW_AS_OF.isoformat(), "cash": "5000",
                "positions": [{"symbol": "DEMO", "asset_type": "equity",
                               "quantity": "100", "price": "50"}]}
    portfolio = snapshot_report(snapshot, now=PREVIEW_AS_OF)
    outcomes = {}
    for terminal in ("0", "48", "60"):
        outcomes[terminal] = standard_option_payoff(
            strategy="cash_secured_put", contracts=1, strike="50",
            premium_per_share="2", terminal_price=terminal, fees="0",
            available_cash="5000")
    if Decimal(outcomes["48"]["expiration_pnl"]) != 0:
        raise AssertionError("Synthetic preview breakeven is inconsistent")
    return {"portfolio": portfolio, "put_outcomes": outcomes,
            "model_status": "fixed synthetic values calculated by atlas.risk"}
