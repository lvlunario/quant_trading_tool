from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from atlas.ingestion import ImportRow, parse_envelope, reconcile, reconcile_envelope


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


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 12, 11, tzinfo=timezone.utc)
        self.payload = {
            'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
            'source_type': 'normalized_synthetic', 'source_id': 'SRC_12345678',
            'as_of': self.now.isoformat(), 'expected_totals': {'ACCT_ALPHA': '100'},
            'rows': [
                {'account_alias': 'ACCT_ALPHA', 'asset_type': 'equity', 'symbol': 'DEMO',
                 'quantity': '2.5', 'price': '10', 'market_value': '25'},
                {'account_alias': 'ACCT_ALPHA', 'asset_type': 'cash', 'symbol': '',
                 'quantity': '0', 'price': '0', 'market_value': '75'},
            ]}

    def test_versioned_envelope_reconciles(self):
        result = reconcile_envelope(self.payload, now=self.now)
        self.assertEqual(result['status'], 'reconciled')
        self.assertEqual(result['publishable_row_count'], 2)
        self.assertEqual(result['account_totals'], {'ACCT_ALPHA': '100'})

    def test_user_export_mode_requires_matching_source(self):
        payload = dict(self.payload, mode='user_export', source_type='normalized_user_export')
        self.assertEqual(parse_envelope(payload, now=self.now).mode, 'user_export')
        with self.assertRaisesRegex(ValueError, 'invalid_mode_source'):
            parse_envelope(dict(payload, source_type='normalized_synthetic'), now=self.now)

    def test_strict_schema_currency_and_source_id(self):
        for update, code in (({'schema_version': 2}, 'unsupported_schema'),
                             ({'currency': 'PHP'}, 'unsupported_currency'),
                             ({'source_id': 'account-1234'}, 'invalid_source_id')):
            with self.subTest(update=update), self.assertRaisesRegex(ValueError, code):
                parse_envelope(dict(self.payload, **update), now=self.now)
        extra = dict(self.payload, unexpected='value')
        with self.assertRaisesRegex(ValueError, 'unsupported_schema'):
            parse_envelope(extra, now=self.now)

    def test_as_of_must_be_aware_current_and_not_future(self):
        values = ((self.now - timedelta(days=5)).isoformat(),
                  (self.now + timedelta(seconds=1)).isoformat(),
                  self.now.replace(tzinfo=None).isoformat())
        for value in values:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'stale_or_invalid_as_of'):
                parse_envelope(dict(self.payload, as_of=value), now=self.now)

    def test_malformed_row_becomes_safe_blocked_outcome(self):
        payload = dict(self.payload, rows=[{'sensitive': 'do-not-echo'}])
        result = reconcile_envelope(payload, now=self.now)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['outcomes'][0]['code'], 'invalid_row')
        self.assertNotIn('do-not-echo', repr(result))
