from dataclasses import replace
from decimal import Decimal
import unittest

from atlas.synthetic_execution import (
    ExecutionPolicy, SyntheticBar, TargetState, run_long_cash_ledger,
)


class SyntheticExecutionTests(unittest.TestCase):
    def setUp(self):
        self.bars = tuple(SyntheticBar(i, Decimal(str(open_price)),
                                       Decimal(str(close_price)))
                          for i, open_price, close_price in (
                              (0, 9, 10), (1, 10, 11), (2, 11, 12),
                              (3, 12, 11), (4, 9, 10), (5, 8, 9)))

    def test_base_case_matches_independent_entry_and_exit_arithmetic(self):
        ledger = run_long_cash_ledger(
            self.bars, (TargetState(0, Decimal('1')),
                        TargetState(2, Decimal('0'))),
            initial_cash=Decimal('1001'), policy=ExecutionPolicy(10))
        entry, exit_fill = ledger.fills
        self.assertEqual(
            (entry.execution_session, entry.quantity, entry.traded_notional,
             entry.transaction_cost, entry.cash_after),
            (1, Decimal('100'), Decimal('1000'), Decimal('1'), Decimal('0')))
        self.assertEqual(entry.traded_notional + entry.transaction_cost,
                         ledger.initial_cash)
        self.assertEqual(
            (exit_fill.execution_session, exit_fill.traded_notional,
             exit_fill.transaction_cost, exit_fill.cash_after),
            (3, Decimal('1200'), Decimal('1.2'), Decimal('1198.8')))
        self.assertEqual((ledger.ending_cash, ledger.ending_shares,
                          ledger.ending_marked_value),
                         (Decimal('1198.8'), Decimal('0'), Decimal('1198.8')))
        self.assertTrue(ledger.synthetic_only)
        self.assertFalse(ledger.investment_performance_established)

    def test_adverse_case_uses_two_session_delay_and_25_bps_per_side(self):
        ledger = run_long_cash_ledger(
            self.bars, (TargetState(0, Decimal('1')),
                        TargetState(2, Decimal('0'))),
            initial_cash=Decimal('110.275'), policy=ExecutionPolicy(25, 2))
        entry, exit_fill = ledger.fills
        self.assertEqual(
            (entry.execution_session, entry.quantity, entry.transaction_cost),
            (2, Decimal('10'), Decimal('0.275')))
        self.assertEqual(
            (exit_fill.execution_session, exit_fill.traded_notional,
             exit_fill.transaction_cost, exit_fill.cash_after),
            (4, Decimal('90'), Decimal('0.225'), Decimal('89.775')))

    def test_fifo_overlap_matches_independent_delayed_arithmetic(self):
        ledger = run_long_cash_ledger(
            self.bars, (TargetState(0, Decimal('1')),
                        TargetState(1, Decimal('0'))),
            initial_cash=Decimal('110.275'),
            policy=ExecutionPolicy(25, 2, 'fifo'))
        entry, exit_fill = ledger.fills
        self.assertEqual(
            (entry.decision_session, entry.execution_session, entry.quantity,
             entry.transaction_cost),
            (0, 2, Decimal('10'), Decimal('0.275')))
        self.assertEqual(
            (exit_fill.decision_session, exit_fill.execution_session,
             exit_fill.traded_notional, exit_fill.transaction_cost,
             exit_fill.cash_after),
            (1, 3, Decimal('120'), Decimal('0.300'), Decimal('119.700')))

    def test_fifo_repeated_pending_target_is_noop_at_execution(self):
        ledger = run_long_cash_ledger(
            self.bars, (TargetState(0, Decimal('1')),
                        TargetState(1, Decimal('1')),
                        TargetState(2, Decimal('0'))),
            initial_cash=Decimal('110'),
            policy=ExecutionPolicy(0, 2, 'fifo'))
        self.assertEqual(
            tuple((fill.decision_session, fill.execution_session)
                  for fill in ledger.fills), ((0, 2), (2, 4)))
        self.assertEqual(ledger.ending_cash, Decimal('90'))
        self.assertEqual(ledger.ending_shares, Decimal('0'))

    def test_repeated_target_creates_no_trade_or_cost(self):
        ledger = run_long_cash_ledger(
            self.bars, (TargetState(0, Decimal('1')),
                        TargetState(2, Decimal('1'))),
            initial_cash=Decimal('1001'), policy=ExecutionPolicy(10))
        self.assertEqual(len(ledger.fills), 1)
        self.assertEqual(ledger.ending_shares, Decimal('100'))
        self.assertEqual(ledger.ending_marked_value, Decimal('900'))

    def test_missing_events_fail_instead_of_backfilling(self):
        cases = (
            ((TargetState(7, Decimal('1')),), 'missing_decision_event'),
            ((TargetState(5, Decimal('1')),), 'missing_execution_event'),
        )
        for signals, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                run_long_cash_ledger(
                    self.bars, signals, initial_cash=Decimal('1001'),
                    policy=ExecutionPolicy(10))

    def test_invalid_prices_targets_policy_and_cash_are_rejected(self):
        for args in ((0, Decimal('0'), Decimal('1')),
                     (0, Decimal('NaN'), Decimal('1')),
                     (True, Decimal('1'), Decimal('1'))):
            with self.subTest(bar=args), self.assertRaises(ValueError):
                SyntheticBar(*args)
        for exposure in (Decimal('-1'), Decimal('.5'), Decimal('NaN'), 1):
            with self.subTest(exposure=exposure), self.assertRaises(ValueError):
                TargetState(0, exposure)
        for args in ((-1,), (10001,), (10, 0), (True,), (10, True),
                     (10, 1, 'replace'), (10, 1, None)):
            with self.subTest(policy=args), self.assertRaises(ValueError):
                ExecutionPolicy(*args)
        for cash in (Decimal('0'), Decimal('-1'), Decimal('NaN'), 100):
            with self.subTest(cash=cash), self.assertRaises(ValueError):
                run_long_cash_ledger(
                    self.bars, (TargetState(0, Decimal('1')),),
                    initial_cash=cash, policy=ExecutionPolicy(10))

    def test_unsorted_duplicate_and_overlapping_inputs_fail_closed(self):
        duplicate_bar = self.bars + (self.bars[-1],)
        reversed_signals = (TargetState(2, Decimal('0')),
                            TargetState(0, Decimal('1')))
        cases = (
            (duplicate_bar, (TargetState(0, Decimal('1')),),
             'bars_must_be_unique_and_chronological'),
            (self.bars, reversed_signals,
             'signals_must_be_unique_and_chronological'),
            (self.bars, (TargetState(0, Decimal('1')),
                         TargetState(0, Decimal('0'))),
             'signals_must_be_unique_and_chronological'),
        )
        for bars, signals, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                run_long_cash_ledger(
                    bars, signals, initial_cash=Decimal('1001'),
                    policy=ExecutionPolicy(10))

        sparse = self.bars[:2] + (replace(self.bars[2], session=1),)
        with self.assertRaisesRegex(ValueError, 'bars_must_be_unique_and_chronological'):
            run_long_cash_ledger(
                sparse, (TargetState(0, Decimal('1')),),
                initial_cash=Decimal('1001'), policy=ExecutionPolicy(10))

        with self.assertRaisesRegex(ValueError, 'overlapping_execution_event'):
            run_long_cash_ledger(
                self.bars, (TargetState(0, Decimal('1')),
                            TargetState(1, Decimal('0'))),
                initial_cash=Decimal('1001'), policy=ExecutionPolicy(10, 2))

    def test_inputs_must_be_typed_tuples(self):
        signal = TargetState(0, Decimal('1'))
        for bars, signals, policy in (
                (list(self.bars), (signal,), ExecutionPolicy(10)),
                (self.bars, [signal], ExecutionPolicy(10)),
                ((object(),), (signal,), ExecutionPolicy(10)),
                (self.bars, (object(),), ExecutionPolicy(10)),
                (self.bars, (signal,), object())):
            with self.subTest(), self.assertRaises(ValueError):
                run_long_cash_ledger(
                    bars, signals, initial_cash=Decimal('1001'), policy=policy)


if __name__ == '__main__':
    unittest.main()
