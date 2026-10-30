from datetime import datetime, timedelta, timezone
from dataclasses import replace
import unittest

from atlas.broker_mapping import (MappingProfile, SYNTHETIC_BROKER_PROFILE,
                                  map_synthetic_broker_export,
                                  parse_synthetic_delimited)


class SyntheticBrokerMappingTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 20, tzinfo=timezone.utc)
        self.payload = {
            'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
            'source_type': 'broker_mapping_synthetic', 'source_id': 'SRC_SYNTHETIC1',
            'as_of': self.now.isoformat(), 'expected_totals': {'ALPHA': '100'},
            'rows': [
                {'account_key': 'ALPHA', 'row_type': 'EQUITY', 'ticker': 'DEMO',
                 'quantity': '2.5', 'price': '10', 'market_value': '25'},
                {'account_key': 'ALPHA', 'row_type': 'CASH', 'ticker': 'IGNORED',
                 'quantity': '0', 'price': '0', 'market_value': '75'},
            ]}

    def map(self, payload=None):
        return map_synthetic_broker_export(payload or self.payload, now=self.now)

    def test_equity_and_cash_map_and_reconcile(self):
        result = self.map()
        self.assertEqual(result['status'], 'reconciled')
        self.assertEqual(result['account_totals'], {'ACCT_ALPHA': '100'})
        self.assertEqual(result['input_row_count'], result['mapped_row_count'])
        self.assertEqual(result['mapping_profile']['rounding_policy'], 'exact')
        self.assertIn('not Fidelity-validated', result['readiness'])

    def test_custom_synthetic_headers_and_row_types_are_profile_driven(self):
        profile = MappingProfile(
            'MAP_CUSTOMSYNTH1', 1, 'USD',
            (('account_key', 'Account'), ('row_type', 'Record Type'),
             ('ticker', 'Instrument'), ('quantity', 'Units'),
             ('price', 'Unit Price'), ('market_value', 'Total Value')),
            (('STOCK', 'equity'), ('AVAILABLE_CASH', 'cash')), 'exact')
        payload = dict(self.payload, rows=[
            {'Account': 'ALPHA', 'Record Type': 'STOCK', 'Instrument': 'DEMO',
             'Units': '2.5', 'Unit Price': '10', 'Total Value': '25'},
            {'Account': 'ALPHA', 'Record Type': 'AVAILABLE_CASH', 'Instrument': '',
             'Units': '0', 'Unit Price': '0', 'Total Value': '75'},
        ])
        result = map_synthetic_broker_export(payload, profile=profile, now=self.now)
        self.assertEqual(result['status'], 'reconciled')
        self.assertEqual(result['mapping_profile']['profile_id'], 'MAP_CUSTOMSYNTH1')

    def test_invalid_or_implicit_profile_semantics_are_rejected(self):
        duplicate_headers = tuple(
            (canonical, 'Amount' if canonical in ('quantity', 'price') else source)
            for canonical, source in SYNTHETIC_BROKER_PROFILE.headers)
        cases = [
            replace(SYNTHETIC_BROKER_PROFILE, schema_version=2),
            replace(SYNTHETIC_BROKER_PROFILE, currency='EUR'),
            replace(SYNTHETIC_BROKER_PROFILE,
                    headers=SYNTHETIC_BROKER_PROFILE.headers[:-1]),
            replace(SYNTHETIC_BROKER_PROFILE, headers=duplicate_headers),
            replace(SYNTHETIC_BROKER_PROFILE, row_types=(('EQUITY', 'security'),)),
            replace(SYNTHETIC_BROKER_PROFILE, rounding_policy='nearest_cent'),
        ]
        for profile in cases:
            with self.subTest(profile=profile), self.assertRaisesRegex(
                    ValueError, 'invalid_mapping_profile'):
                map_synthetic_broker_export(self.payload, profile=profile, now=self.now)

    def test_core_cash_maps_without_ticker(self):
        rows = [dict(self.payload['rows'][0]),
                dict(self.payload['rows'][1], row_type='CORE_CASH')]
        self.assertEqual(self.map(dict(self.payload, rows=rows))['status'], 'reconciled')

    def test_unsupported_option_is_accounted_and_blocks(self):
        option = dict(self.payload['rows'][0], row_type='OPTION', ticker='DEMO_OPT')
        result = self.map(dict(self.payload, rows=self.payload['rows'] + [option]))
        self.assertEqual(result['input_row_count'], 3)
        self.assertEqual(result['outcomes'][-1]['code'], 'unsupported_asset')
        self.assertEqual(result['publishable_row_count'], 0)

    def test_malformed_footer_and_unknown_account_are_not_dropped(self):
        rows = self.payload['rows'] + [
            {'footer': 'sensitive-source-text'},
            dict(self.payload['rows'][0], account_key='UNKNOWN')]
        result = self.map(dict(self.payload, rows=rows))
        self.assertEqual(result['mapped_row_count'], 4)
        self.assertEqual([item['code'] for item in result['outcomes'][-2:]],
                         ['invalid_row', 'invalid_row'])
        self.assertNotIn('sensitive-source-text', repr(result))

    def test_duplicate_cash_is_blocked_after_mapping(self):
        rows = self.payload['rows'] + [dict(self.payload['rows'][1], row_type='CORE_CASH')]
        result = self.map(dict(self.payload, rows=rows, expected_totals={'ALPHA': '175'}))
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual([item['code'] for item in result['outcomes'][-2:]],
                         ['duplicate_position_or_cash', 'duplicate_position_or_cash'])

    def test_total_mismatch_and_stale_source_block(self):
        mismatch = self.map(dict(self.payload, expected_totals={'ALPHA': '101'}))
        self.assertIn('account_total_mismatch', mismatch['errors'])
        stale = dict(self.payload, as_of=(self.now - timedelta(days=5)).isoformat())
        with self.assertRaisesRegex(ValueError, 'stale_or_invalid_as_of'):
            self.map(stale)

    def test_outer_contract_is_strict(self):
        cases = [dict(self.payload, source_type='fidelity'),
                 dict(self.payload, mode='user_export'),
                 dict(self.payload, currency='EUR'),
                 dict(self.payload, schema_version=2),
                 dict(self.payload, unexpected=True)]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.map(payload)

    def test_bad_account_key_and_empty_rows_rejected(self):
        for payload in (dict(self.payload, expected_totals={'1234': '100'}),
                        dict(self.payload, rows=[])):
            with self.assertRaises(ValueError):
                self.map(payload)

    def test_delimited_source_reconciles_and_accounts_for_footers(self):
        source = (b'account_key,row_type,ticker,quantity,price,market_value\n'
                  b'ALPHA,EQUITY,DEMO,2.5,10,25\n'
                  b'ALPHA,CASH,,0,0,75\n'
                  b'ALPHA,ACCOUNT_TOTAL,,,,100\n')
        result = parse_synthetic_delimited(
            source, source_id='SRC_DELIMITED1', as_of=self.now.isoformat(), now=self.now)
        self.assertEqual(result['status'], 'reconciled')
        self.assertEqual(result['parser_contract'], 'synthetic_delimited_v1')
        self.assertEqual((result['header_record_count'], result['position_record_count'],
                          result['footer_record_count'], result['delimited_record_count']),
                         (1, 2, 1, 4))

    def test_delimited_alternate_profile_headers_are_exact(self):
        profile = MappingProfile(
            'MAP_DELIMITED1', 1, 'USD',
            (('account_key', 'Account'), ('row_type', 'Kind'),
             ('ticker', 'Ticker'), ('quantity', 'Quantity'),
             ('price', 'Price'), ('market_value', 'Value')),
            (('STOCK', 'equity'),), 'exact', 'TOTAL')
        source = (b'Account,Kind,Ticker,Quantity,Price,Value\n'
                  b'ALPHA,STOCK,DEMO,2,50,100\n'
                  b'ALPHA,TOTAL,,,,100\n')
        result = parse_synthetic_delimited(
            source, source_id='SRC_DELIMITED2', as_of=self.now.isoformat(),
            profile=profile, now=self.now)
        self.assertEqual(result['status'], 'reconciled')
        self.assertEqual(result['mapping_profile']['profile_id'], 'MAP_DELIMITED1')

    def test_malformed_or_data_after_footer_rows_cannot_disappear(self):
        source = (b'account_key,row_type,ticker,quantity,price,market_value\n'
                  b'ALPHA,CASH,,0,0,100\n'
                  b'bad,row\n'
                  b'ALPHA,ACCOUNT_TOTAL,,,,100\n'
                  b'ALPHA,EQUITY,DEMO,1,1,1\n')
        result = parse_synthetic_delimited(
            source, source_id='SRC_DELIMITED3', as_of=self.now.isoformat(), now=self.now)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['position_record_count'], 3)
        self.assertEqual([item['code'] for item in result['outcomes']],
                         ['ok', 'invalid_row', 'invalid_row'])
        self.assertEqual(result['publishable_row_count'], 0)

    def test_delimited_header_and_footer_contracts_fail_closed(self):
        header = b'account_key,row_type,ticker,quantity,price,market_value\n'
        cases = [
            b'wrong,header\nALPHA,CASH,,0,0,100\n',
            header + b'ALPHA,CASH,,0,0,100\n',
            header + b'ALPHA,CASH,,0,0,100\nALPHA,ACCOUNT_TOTAL,,,,100\n'
            b'ALPHA,ACCOUNT_TOTAL,,,,100\n',
            header + b'ALPHA,ACCOUNT_TOTAL,EXTRA,,,100\n',
        ]
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_synthetic_delimited(
                    source, source_id='SRC_DELIMITED4', as_of=self.now.isoformat(),
                    now=self.now)

    def test_delimited_source_limits_and_encoding(self):
        sources = [b'', b'x' * 1_000_001, b'\xff', b'a\x00b']
        for source in sources:
            with self.subTest(length=len(source)), self.assertRaises(ValueError):
                parse_synthetic_delimited(
                    source, source_id='SRC_DELIMITED5', as_of=self.now.isoformat(),
                    now=self.now)
