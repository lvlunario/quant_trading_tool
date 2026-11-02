from dataclasses import replace
from datetime import date, datetime, timezone
import json
import unittest

from atlas.integrated_readiness import compose_integrated_prototype_readiness
from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.receipts import ImportReceipt
from atlas.weekly_report_readiness import assess_weekly_report_readiness
from atlas.weekly_research_report import build_synthetic_weekly_research_report


class IntegratedPrototypeReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
        names = ('identity', 'source_discovery', 'rights_review',
                 'capture_authorization', 'extraction', 'metric_release')
        counts = (8, 8, 0, 0, 0, 0)
        blockers = ('identity_unresolved', 'source_candidate_missing',
                    'rights_review_incomplete',
                    'capture_authorization_incomplete',
                    'no_authorized_source_bytes',
                    'no_verified_metric_evidence')
        trace = M2AcceptanceTrace(
            self.now, 9,
            tuple(M2GateStage(name, count, 9 - count, blocker)
                  for name, count, blocker in zip(names, counts, blockers)))
        report = build_synthetic_weekly_research_report(
            period_end=date(2026, 11, 2), generated_at=self.now)
        self.research = assess_weekly_report_readiness(report, trace)
        self.portfolio = ImportReceipt(
            1, 'synthetic', 'reconciled', 'not_checked', 3, 0, 3,
            'replay_check_required')
        self.options = build_synthetic_options_acceptance_evidence()

    def compose(self, **changes):
        inputs = {'portfolio': self.portfolio, 'research': self.research,
                  'options': self.options, 'assessed_at': self.now}
        inputs.update(changes)
        return compose_integrated_prototype_readiness(**inputs)

    def test_composes_three_count_only_slices(self):
        summary = self.compose().public_summary()
        self.assertEqual(summary['portfolio']['publishable_rows'], 3)
        self.assertEqual(summary['research']['stage_passed_counts'],
                         [8, 8, 0, 0, 0, 0])
        self.assertEqual(summary['options']['control_count'], 4)
        self.assertEqual(summary['options']['scenario_count'], 2)

    def test_keeps_private_and_action_capabilities_disabled(self):
        summary = self.compose().public_summary()
        self.assertTrue(summary['capabilities']['read_only'])
        for key in ('authentication_implemented',
                    'private_persistence_implemented',
                    'network_retrieval_enabled', 'order_path_enabled'):
            self.assertFalse(summary['capabilities'][key])
        self.assertFalse(summary['release_authorized'])
        self.assertFalse(summary['investment_performance_established'])

    def test_summary_excludes_financial_identifiers_and_values(self):
        payload = json.dumps(self.compose().public_summary()).lower()
        for forbidden in ('account_id', 'source_uri', 'reserved_cash',
                          'strike', 'gross_cumulative_return', 'symbol'):
            self.assertNotIn(forbidden, payload)

    def test_real_or_promoted_inputs_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'invalid_integrated_prototype_readiness'):
            self.compose(portfolio=replace(self.portfolio, mode='user_export'))
        with self.assertRaisesRegex(
                ValueError, 'invalid_integrated_prototype_readiness'):
            self.compose(portfolio=replace(
                self.portfolio, replay='recorded', decision='eligible'))

    def test_timestamp_mismatch_and_wrong_types_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, 'invalid_integrated_prototype_readiness'):
            self.compose(assessed_at=datetime(2026, 11, 2, 12, 0,
                                              tzinfo=timezone.utc))
        with self.assertRaisesRegex(
                ValueError, 'invalid_integrated_prototype_readiness'):
            self.compose(options={})


if __name__ == '__main__':
    unittest.main()
