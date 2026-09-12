from dataclasses import replace
from decimal import Decimal
import unittest

from atlas.ingestion import ImportRow, reconcile


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.equity = ImportRow('ACCT_ALPHA', 'equity', 'DEMO', '2.5', '10', '25')
        self.cash = ImportRow('ACCT_ALPHA', 'cash', '', '0', '0', '75')
        self.rows = [self.equity, self.cash]

    def test_fractional_equity_and_cash_reconcile(self):
        result = reconcile(self.rows, {'ACCT_ALPHA': '100'})
        self.assertEqual(result.status, 'reconciled')
        self.assertEqual(result.account_totals, (('ACCT_ALPHA', Decimal('100')),))
        self.assertEqual(len(result.outcomes), 2)

    def test_core_cash_supported_without_duplicate_cash(self):
        result = reconcile([self.equity, replace(self.cash, asset_type='core_cash')], {'ACCT_ALPHA': '100'})
        self.assertEqual(result.status, 'reconciled')

    def test_cash_and_core_cash_both_rejected(self):
        rows = self.rows + [replace(self.cash, asset_type='core_cash')]
        result = reconcile(rows, {'ACCT_ALPHA': '175'})
        self.assertEqual([o.status for o in result.outcomes], ['accepted', 'rejected', 'rejected'])
        self.assertEqual(result.rows, ())
        self.assertEqual(result.account_totals, ())

    def test_duplicate_positions_both_rejected(self):
        result = reconcile([self.equity, self.equity], {'ACCT_ALPHA': '50'})
        self.assertTrue(all(o.code == 'duplicate_position_or_cash' for o in result.outcomes))

    def test_same_symbol_in_separate_accounts_valid(self):
        result = reconcile([self.equity, replace(self.equity, account_alias='ACCT_BETA')],
                           {'ACCT_ALPHA': '25', 'ACCT_BETA': '25'})
        self.assertEqual(result.status, 'reconciled')

    def test_total_mismatch_blocks_publication(self):
        result = reconcile(self.rows, {'ACCT_ALPHA': '100.01'})
        self.assertIn('account_total_mismatch', result.errors)
        self.assertEqual(result.rows, ())

    def test_position_value_mismatch(self):
        result = reconcile([replace(self.equity, market_value='24')], {'ACCT_ALPHA': '24'})
        self.assertEqual(result.outcomes[0].code, 'position_value_mismatch')

    def test_unknown_and_missing_accounts_block(self):
        result = reconcile(self.rows, {'ACCT_BETA': '100'})
        self.assertIn('account_coverage_mismatch', result.errors)
        self.assertTrue(all(o.code == 'unknown_account' for o in result.outcomes))

    def test_unsupported_option_cannot_disappear(self):
        result = reconcile(self.rows + [replace(self.equity, asset_type='option', symbol='OPTION')],
                           {'ACCT_ALPHA': '100'})
        self.assertEqual(result.outcomes[-1].code, 'unsupported_asset')
        self.assertEqual(len(result.outcomes), 3)
        self.assertEqual(result.status, 'blocked')

    def test_numeric_failures_return_safe_codes(self):
        for bad in ('NaN', '-5', '', '1e1000000', '0.123456789', 'sensitive-test-data', 1.0):
            with self.subTest(bad=bad):
                result = reconcile([replace(self.equity, quantity=bad)], {'ACCT_ALPHA': '25'})
                self.assertEqual(result.outcomes[0].code, 'invalid_decimal')
                self.assertNotIn('sensitive-test-data', repr(result))

    def test_malformed_row_accounted_for(self):
        result = reconcile([None, self.cash], {'ACCT_ALPHA': '75'})
        self.assertEqual(result.outcomes[0].code, 'invalid_row')
        self.assertEqual(result.rows, ())

    def test_invalid_cash_or_symbol(self):
        for row in (replace(self.cash, symbol='CORE'), replace(self.equity, symbol='demo')):
            with self.subTest(row=row):
                self.assertEqual(reconcile([row], {'ACCT_ALPHA': '25'}).status, 'blocked')

    def test_empty_input_missing_totals_and_bad_alias_raise(self):
        for rows, totals in (([], {'ACCT_ALPHA': '100'}), (self.rows, {}), (self.rows, {'12345': '100'})):
            with self.assertRaises(ValueError):
                reconcile(rows, totals)

    def test_replay_is_deterministic_and_does_not_mutate(self):
        first = reconcile(self.rows, {'ACCT_ALPHA': '100'})
        self.assertEqual(first, reconcile(self.rows, {'ACCT_ALPHA': '100'}))
        self.assertEqual(self.rows, [self.equity, self.cash])
