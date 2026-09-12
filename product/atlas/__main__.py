"""Run from product/: python -m atlas --demo, or --snapshot /private/input.json."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from .risk import snapshot_report, standard_option_payoff


def main():
    parser = argparse.ArgumentParser(description="Atlas research kernel; no live trading")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    try:
        if args.demo:
            snapshot = {"schema_version": 1, "mode": "synthetic", "currency": "USD",
                        "as_of": datetime.now(timezone.utc).isoformat(), "cash": "20000",
                        "positions": [{"symbol": "DEMO", "asset_type": "equity",
                                       "quantity": "100", "price": "100"}]}
            report = {"portfolio": snapshot_report(snapshot), "hypothetical_put": standard_option_payoff(
                strategy="cash_secured_put", contracts=1, strike="90", premium_per_share="2",
                terminal_price="60", available_cash="20000", fees="1")}
        else:
            if args.snapshot.stat().st_size > 1_000_000:
                raise ValueError("Input exceeds 1 MB limit")
            report = snapshot_report(json.loads(args.snapshot.read_text()))
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        # Do not echo raw account content or file paths into logs.
        parser.exit(2, f"Input rejected ({type(error).__name__}); see input contract.\n")


if __name__ == "__main__":
    main()
