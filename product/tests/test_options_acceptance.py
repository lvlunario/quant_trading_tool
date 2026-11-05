from datetime import datetime, timedelta, timezone
import json
import subprocess
import sys
import unittest

from atlas.options_acceptance import (
    OptionAcceptanceBlocked,
    OptionScenarioRequest,
    build_synthetic_options_acceptance_evidence,
    reserve_option_collateral,
)


class OptionsAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 29, 11, 0, tzinfo=timezone.utc)
        self.fresh = self.now - timedelta(minutes=5)

    def request(self, scenario_id='SYNOPT_PUT1', strategy='cash_secured_put',
                instrument_id='SYN_ALPHA', contracts=1, strike='50',
                fees='1', chain_as_of=None):
        return OptionScenarioRequest(
            scenario_id, instrument_id, strategy, contracts, strike, fees,
            chain_as_of or self.fresh)

    def reserve(self, requests, cash='5001', shares=None, **changes):
        args = dict(available_cash=cash,
                    unencumbered_shares=shares or {}, now=self.now)
        args.update(changes)
        return reserve_option_collateral(requests, **args)

    def test_reserves_gross_put_cash_and_call_shares(self):
        receipt = self.reserve(
            (self.request(), self.request(
                'SYNOPT_CALL1', 'covered_call', 'SYN_BETA')),
            shares={'SYN_BETA': '100'})
        self.assertEqual(receipt.reserved_cash, '5001')
        self.assertEqual(receipt.reserved_shares, (('SYN_BETA', 100),))
        self.assertFalse(receipt.actionable_ranking_authorized)

    def test_put_cash_cannot_be_counted_twice(self):
        with self.assertRaisesRegex(
                OptionAcceptanceBlocked,
                '^cash_collateral_double_use_or_shortfall$'):
            self.reserve((self.request(), self.request(
                'SYNOPT_PUT2', instrument_id='SYN_BETA')))

    def test_call_shares_cannot_be_counted_twice(self):
        requests = (
            self.request('SYNOPT_CALL1', 'covered_call', 'SYN_ALPHA'),
            self.request('SYNOPT_CALL2', 'covered_call', 'SYN_ALPHA'),
        )
        with self.assertRaisesRegex(
                OptionAcceptanceBlocked,
                '^share_collateral_double_use_or_shortfall$'):
            self.reserve(requests, shares={'SYN_ALPHA': 100})

    def test_stale_future_and_naive_chains_block(self):
        values = (self.now - timedelta(minutes=16),
                  self.now + timedelta(microseconds=1),
                  self.fresh.replace(tzinfo=None))
        for index, value in enumerate(values):
            request = self.request(f'SYNOPT_BAD{index}', chain_as_of=value)
            with self.subTest(value=value), self.assertRaisesRegex(
                    OptionAcceptanceBlocked, '^chain_not_fresh$'):
                self.reserve((request,))

    def test_batch_identity_and_context_are_strict(self):
        request = self.request()
        for requests in ((), (request, request)):
            with self.subTest(requests=requests), self.assertRaises(ValueError):
                self.reserve(requests)
        with self.assertRaises(ValueError):
            self.reserve((request,), shares={'ACTUAL': 100})

    def test_requests_reject_real_mode_and_bad_contracts(self):
        with self.assertRaises(ValueError):
            OptionScenarioRequest('SYNOPT_PUT1', 'SYN_ALPHA',
                                  'cash_secured_put', 1, '50', '1',
                                  self.fresh, source_mode='user_export')
        for contracts in (0, 1.5, True):
            with self.subTest(contracts=contracts), self.assertRaises(ValueError):
                self.request(contracts=contracts)

    def test_fixed_evidence_is_deterministic_and_non_promotional(self):
        first = build_synthetic_options_acceptance_evidence()
        second = build_synthetic_options_acceptance_evidence()
        self.assertEqual(first, second)
        self.assertEqual(first.evidence_sha256, second.evidence_sha256)
        summary = first.public_summary()
        self.assertEqual(summary['status'], 'ready_for_founder_scenario_review')
        self.assertTrue(all(summary['controls'].values()))
        self.assertFalse(summary['founder_acceptance_recorded'])
        self.assertFalse(summary['real_chain_validated'])
        self.assertFalse(summary['actionable_ranking_authorized'])

    def test_public_summary_excludes_collateral_values_and_instruments(self):
        payload = json.dumps(
            build_synthetic_options_acceptance_evidence().public_summary(),
            sort_keys=True)
        for forbidden in ('5001', 'SYN_ALPHA', 'SYN_BETA', 'reserved_cash',
                          'reserved_shares', 'chain_as_of'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_module_report_matches_typed_evidence(self):
        process = subprocess.run(
            [sys.executable, '-m', 'atlas.options_acceptance'],
            check=True, capture_output=True, text=True)
        report = json.loads(process.stdout)
        evidence = build_synthetic_options_acceptance_evidence()
        self.assertEqual(report['evidence_sha256'], evidence.evidence_sha256)
        report.pop('evidence_sha256')
        self.assertEqual(report, evidence.public_summary())


if __name__ == '__main__':
    unittest.main()
