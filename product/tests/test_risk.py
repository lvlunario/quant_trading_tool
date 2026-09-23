from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest
from atlas.risk import amount, snapshot_report, standard_option_payoff


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 12, tzinfo=timezone.utc)
        self.snapshot = {"schema_version": 1, "mode": "synthetic", "currency": "USD",
                         "as_of": self.now.isoformat(), "cash": "5000",
                         "positions": [{"symbol": "DEMO", "asset_type": "equity",
                                        "quantity": "100", "price": "50"}]}

    def put(self, **changes):
        args = dict(strategy="cash_secured_put", contracts=1, strike="50",
                    premium_per_share="2", terminal_price="60", fees="1", available_cash="5001")
        args.update(changes)
        return standard_option_payoff(**args)

    def call(self, **changes):
        args = dict(strategy="covered_call", contracts=1, strike="55", premium_per_share="2",
                    terminal_price="100", stock_entry="50", shares=100, fees="1")
        args.update(changes)
        return standard_option_payoff(**args)

    def test_decimal_rejects_bad_inputs(self):
        for value in ("NaN", "Infinity", "-1", True, 1.2, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                amount(value)

    def test_snapshot_value_and_weights(self):
        report = snapshot_report(self.snapshot, now=self.now)
        self.assertEqual(Decimal(report["total_value"]), Decimal(10000))
        self.assertEqual(Decimal(report["cash_weight"]), Decimal("0.5"))
        self.assertEqual(Decimal(report["equity_weights"]["DEMO"]), Decimal("0.5"))

    def test_stale_future_naive_rejected(self):
        for timestamp in (self.now-timedelta(days=5), self.now+timedelta(seconds=1), self.now.replace(tzinfo=None)):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                snapshot_report(dict(self.snapshot, as_of=timestamp.isoformat()), now=self.now)

    def test_duplicate_positions_rejected(self):
        self.snapshot["positions"] *= 2
        with self.assertRaises(ValueError):
            snapshot_report(self.snapshot, now=self.now)

    def test_option_position_cannot_be_dropped(self):
        self.snapshot["positions"][0]["asset_type"] = "option"
        with self.assertRaises(ValueError):
            snapshot_report(self.snapshot, now=self.now)

    def test_cash_only(self):
        report = snapshot_report(dict(self.snapshot, positions=[]), now=self.now)
        self.assertEqual(Decimal(report["cash_weight"]), 1)

    def test_unsupported_currency(self):
        with self.assertRaises(ValueError):
            snapshot_report(dict(self.snapshot, currency="PHP"), now=self.now)

    def test_put_upside_is_premium_less_fees(self):
        self.assertEqual(Decimal(self.put()["expiration_pnl"]), 199)

    def test_put_bankruptcy_loss(self):
        result = self.put(terminal_price="0")
        self.assertEqual(Decimal(result["expiration_pnl"]), -4801)
        self.assertEqual(Decimal(result["maximum_loss"]), 4801)

    def test_put_breakeven(self):
        result = self.put(terminal_price=self.put()["breakeven"])
        self.assertEqual(Decimal(result["expiration_pnl"]), 0)

    def test_reserve_does_not_spend_unreceived_premium(self):
        with self.assertRaises(ValueError):
            self.put(available_cash="5000")

    def test_call_caps_upside(self):
        self.assertEqual(Decimal(self.call()["expiration_pnl"]), 699)
        self.assertEqual(self.call(terminal_price="55")["expiration_pnl"], self.call()["expiration_pnl"])

    def test_call_bankruptcy_loss(self):
        self.assertEqual(Decimal(self.call(terminal_price="0")["expiration_pnl"]), -4801)

    def test_call_breakeven(self):
        self.assertEqual(Decimal(self.call(terminal_price=self.call()["breakeven"])["expiration_pnl"]), 0)

    def test_cannot_write_uncovered_call(self):
        with self.assertRaises(ValueError):
            self.call(shares=99)

    def test_adjusted_and_fractional_contracts_rejected(self):
        for changes in ({"multiplier": 10}, {"contracts": 1.5}, {"contracts": True}, {"contracts": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.put(**changes)

    def test_scenario_pnl_respects_bounds(self):
        for terminal in range(0, 101):
            for result in (self.put(terminal_price=terminal), self.call(terminal_price=terminal)):
                self.assertGreaterEqual(Decimal(result["expiration_pnl"]), -Decimal(result["maximum_loss"]))
                self.assertLessEqual(Decimal(result["expiration_pnl"]), Decimal(result["maximum_pnl"]))


if __name__ == "__main__":
    unittest.main()
