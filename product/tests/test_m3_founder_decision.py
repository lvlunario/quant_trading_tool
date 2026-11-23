from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.m3_founder_decision import record_m3_founder_decisions
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.selection_freeze import SelectionFreezeCandidate


class M3FounderDecisionTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads((
            Path(__file__).parents[1] / 'fixtures' /
            'm3-selection-freeze-candidate.json').read_text())
        fixture.pop('candidate_sha256')
        self.freeze = SelectionFreezeCandidate(**fixture)
        self.options = build_synthetic_options_acceptance_evidence()
        self.decided_at = datetime(2026, 11, 4, 12, 30,
                                   tzinfo=timezone.utc)

    def record(self, **changes):
        inputs = {'freeze_candidate': self.freeze,
                  'options_evidence': self.options,
                  'decided_at': self.decided_at}
        inputs.update(changes)
        return record_m3_founder_decisions(**inputs)

    def test_records_all_three_actual_dispositions_in_order(self):
        summary = self.record().public_summary()
        self.assertEqual(
            [item['decision'] for item in summary['decisions']],
            ['selection_freeze', 'final_synthetic_holdout',
             'synthetic_options_scenarios'])
        self.assertEqual(summary['m3_readiness'], {
            'ready_count': 5,
            'required_count': 6,
            'remaining_criterion': 'final_holdout_receipt',
        })
        self.assertTrue(summary['selection_frozen'])
        self.assertTrue(summary['holdout_authorized'])
        self.assertFalse(summary['holdout_inspected'])

    def test_does_not_grant_merge_release_real_data_or_trading_authority(self):
        summary = self.record().public_summary()
        for key in ('milestone_acceptance_recorded', 'release_authorized',
                    'real_data_validated',
                    'investment_performance_established', 'merge_authorized',
                    'trading_authorized'):
            self.assertFalse(summary[key])

    def test_decision_is_hash_bound_to_exact_prior_evidence(self):
        record = self.record()
        self.assertEqual(record.freeze_candidate_sha256,
                         self.freeze.candidate_sha256)
        self.assertEqual(record.options_evidence_sha256,
                         self.options.evidence_sha256)
        self.assertEqual(record.decision_sha256, record.decision_sha256)
        self.assertEqual(len(record.decision_sha256), 64)

    def test_checked_in_decision_matches_exact_record(self):
        checked_in = json.loads((
            Path(__file__).parents[1] / 'fixtures' /
            'm3-founder-decision.json').read_text())
        record = self.record()
        expected = record.public_summary()
        expected.update({
            'freeze_candidate_sha256': record.freeze_candidate_sha256,
            'options_evidence_sha256': record.options_evidence_sha256,
            'decision_sha256': record.decision_sha256,
        })
        self.assertEqual(checked_in, expected)

    def test_public_summary_excludes_private_and_financial_values(self):
        payload = json.dumps(self.record().public_summary()).lower()
        for forbidden in ('account_id', 'source_uri', 'reserved_cash',
                          'strike', 'gross_cumulative_return', 'symbol'):
            self.assertNotIn(forbidden, payload)

    def test_adjacent_authority_cannot_be_promoted(self):
        record = self.record()
        for change in ({'holdout_inspected': True},
                       {'milestone_accepted': True},
                       {'release_authorized': True},
                       {'real_data_validated': True},
                       {'merge_authorized': True},
                       {'trading_authorized': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(record, **change)

    def test_wrong_or_promoted_evidence_fails_closed(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_m3_founder_decision_input'):
            self.record(freeze_candidate=object())
        with self.assertRaisesRegex(ValueError,
                                    'invalid_selection_freeze_candidate'):
            self.record(freeze_candidate=replace(
                self.freeze, recommended_disposition='review_later'))
        with self.assertRaisesRegex(ValueError,
                                    'invalid_m3_founder_decision_record'):
            self.record(decided_at=datetime(2026, 11, 4, 12, 30))


if __name__ == '__main__':
    unittest.main()
