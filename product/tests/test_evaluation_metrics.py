from dataclasses import replace
from decimal import Decimal
import unittest

from atlas.evaluation_metrics import EvaluationMetrics, calculate_evaluation_metrics
from atlas.synthetic_execution import ExecutionPolicy, SyntheticBar, TargetState


D = Decimal


class EvaluationMetricsTests(unittest.TestCase):
    def test_round_trip_metrics_match_independent_arithmetic(self):
        bars = (
            SyntheticBar(0, D('10'), D('10')),
            SyntheticBar(1, D('10'), D('12')),
            SyntheticBar(2, D('12'), D('9')),
            SyntheticBar(3, D('9'), D('11')),
        )
        metrics = calculate_evaluation_metrics(
            bars, (TargetState(0, D('1')), TargetState(1, D('0'))),
            initial_cash=D('1010'), policy=ExecutionPolicy(100, 1))

        # Gross: 101 shares bought at 10 and sold at 12 = 1,212.
        self.assertEqual(metrics.gross_cumulative_return, D('202') / D('1010'))
        # Net: 1,000 notional + 10 entry cost; 1,200 sale - 12 exit cost.
        self.assertEqual(
            metrics.net_cumulative_return, D('1188') / D('1010') - D('1'))
        self.assertEqual(metrics.maximum_drawdown, D('12') / D('1200'))
        self.assertEqual(
            metrics.turnover_on_initial_capital, D('2200') / D('1010'))
        self.assertEqual(metrics.long_exposure_fraction, D('1') / D('4'))
        self.assertEqual(metrics.marked_session_count, 4)

    def test_drawdown_uses_initial_capital_and_running_close_peak(self):
        bars = (
            SyntheticBar(0, D('100'), D('100')),
            SyntheticBar(1, D('100'), D('120')),
            SyntheticBar(2, D('100'), D('90')),
            SyntheticBar(3, D('100'), D('110')),
        )
        metrics = calculate_evaluation_metrics(
            bars, (TargetState(0, D('1')),), initial_cash=D('100'),
            policy=ExecutionPolicy(0, 1))
        self.assertEqual(metrics.gross_cumulative_return, D('0.10'))
        self.assertEqual(metrics.net_cumulative_return, D('0.10'))
        self.assertEqual(metrics.maximum_drawdown, D('0.25'))
        self.assertEqual(metrics.turnover_on_initial_capital, D('1'))
        self.assertEqual(metrics.long_exposure_fraction, D('0.75'))

    def test_entry_cost_drawdown_is_measured_from_initial_capital(self):
        bars = (
            SyntheticBar(0, D('10'), D('10')),
            SyntheticBar(1, D('10'), D('10')),
        )
        metrics = calculate_evaluation_metrics(
            bars, (TargetState(0, D('1')),), initial_cash=D('101'),
            policy=ExecutionPolicy(100, 1))
        self.assertEqual(metrics.gross_cumulative_return, D('0'))
        self.assertEqual(
            metrics.net_cumulative_return, D('100') / D('101') - D('1'))
        self.assertEqual(metrics.maximum_drawdown, D('1') / D('101'))
        self.assertEqual(metrics.long_exposure_fraction, D('0.5'))

    def test_gross_replay_preserves_delay_and_fifo_policy(self):
        bars = tuple(
            SyntheticBar(i, D(str(10 + i)), D(str(10 + i))) for i in range(5))
        metrics = calculate_evaluation_metrics(
            bars, (
                TargetState(0, D('1')), TargetState(1, D('0')),
                TargetState(2, D('1'))),
            initial_cash=D('100'), policy=ExecutionPolicy(25, 2, 'fifo'))
        self.assertEqual(metrics.marked_session_count, 5)
        self.assertGreater(metrics.gross_cumulative_return,
                           metrics.net_cumulative_return)
        self.assertGreater(metrics.turnover_on_initial_capital, D('0'))

    def test_invalid_ledger_inputs_remain_fail_closed(self):
        bars = (SyntheticBar(0, D('10'), D('10')),)
        with self.assertRaisesRegex(ValueError, 'missing_execution_event'):
            calculate_evaluation_metrics(
                bars, (TargetState(0, D('1')),), initial_cash=D('100'),
                policy=ExecutionPolicy(0, 1))

    def test_metric_receipt_cannot_claim_holdout_or_performance(self):
        metrics = EvaluationMetrics(D('0'), D('0'), D('0'), D('0'), D('0'), 1)
        for change in (
                {'synthetic_only': False}, {'holdout_inspected': True},
                {'investment_performance_established': True},
                {'maximum_drawdown': D('-0.01')},
                {'long_exposure_fraction': D('1.01')},
                {'marked_session_count': 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(metrics, **change)


if __name__ == '__main__':
    unittest.main()
