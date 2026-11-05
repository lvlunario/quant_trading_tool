from dataclasses import replace
from decimal import Decimal
import unittest

from atlas.synthetic_execution import SyntheticBar
from atlas.synthetic_series import (
    GENERATOR_VERSION, REGISTERED_LOOKBACK, REGISTERED_SEED,
    REGISTERED_SESSIONS, generate_bars, registered_series,
    trailing_target_changes,
)


class SyntheticSeriesTests(unittest.TestCase):
    def test_registered_series_is_exact_and_reproducible(self):
        first = registered_series()
        second = registered_series()
        self.assertEqual(first, second)
        self.assertEqual(
            (first.generator_version, first.seed, len(first.bars),
             first.lookback_sessions),
            (GENERATOR_VERSION, REGISTERED_SEED, REGISTERED_SESSIONS,
             REGISTERED_LOOKBACK))
        self.assertTrue(first.synthetic_only)
        self.assertFalse(first.holdout_inspected)
        self.assertFalse(first.investment_performance_established)

    def test_registered_fixture_values_and_targets_are_locked(self):
        series = registered_series()
        self.assertEqual(
            tuple((row.session, row.open_price, row.close_price)
                  for row in series.bars[:3]),
            ((0, Decimal('99.9700'), Decimal('99.7901')),
             (1, Decimal('99.8600'), Decimal('99.4606')),
             (2, Decimal('99.4109'), Decimal('99.5998'))))
        self.assertEqual(
            tuple((row.decision_session, row.target_exposure)
                  for row in series.targets),
            ((20, Decimal('0')), (35, Decimal('1')), (55, Decimal('0')),
             (74, Decimal('1')), (79, Decimal('0')), (80, Decimal('1')),
             (81, Decimal('0')), (91, Decimal('1')), (92, Decimal('0')),
             (102, Decimal('1')), (135, Decimal('0'))))

    def test_targets_use_current_and_trailing_closes_then_exclude_holdout(self):
        bars = tuple(SyntheticBar(i, Decimal('1'), value) for i, value in enumerate((
            Decimal('10'), Decimal('11'), Decimal('9'), Decimal('12'),
            Decimal('8'), Decimal('13'), Decimal('7'), Decimal('14'))))
        targets = trailing_target_changes(
            bars, lookback_sessions=2, holdout_start=6)
        self.assertEqual(
            tuple((row.decision_session, row.target_exposure) for row in targets),
            ((2, Decimal('0')), (3, Decimal('1')), (4, Decimal('0')),
             (5, Decimal('1'))))
        self.assertTrue(all(row.decision_session < 6 for row in targets))

    def test_different_seed_changes_invented_series(self):
        self.assertNotEqual(generate_bars(seed=1, sessions=5),
                            generate_bars(seed=2, sessions=5))

    def test_invalid_generator_inputs_fail_closed(self):
        for seed, sessions in ((0, 2), (-1, 2), (2 ** 32, 2),
                               (True, 2), (1, 1), (1, 10001), (1, True)):
            with self.subTest(seed=seed, sessions=sessions), self.assertRaises(ValueError):
                generate_bars(seed=seed, sessions=sessions)

    def test_invalid_signal_contracts_fail_closed(self):
        bars = generate_bars(seed=1, sessions=8)
        cases = (
            (list(bars), 2, 6), ((object(),), 2, 6),
            (bars, 0, 6), (bars, 8, 6), (bars, True, 6),
            (bars, 2, 2), (bars, 2, 8), (bars, 2, True),
            ((bars[0], replace(bars[1], session=3)) + bars[2:], 2, 6),
        )
        for candidate, lookback, holdout in cases:
            with self.subTest(lookback=lookback, holdout=holdout), self.assertRaises(ValueError):
                trailing_target_changes(
                    candidate, lookback_sessions=lookback,
                    holdout_start=holdout)


if __name__ == '__main__':
    unittest.main()
