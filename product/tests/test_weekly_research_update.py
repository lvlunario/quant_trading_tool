"""The weekly delta packet must preserve identity and evidence boundaries."""
from pathlib import Path
import unittest


class WeeklyResearchUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).parents[1] / 'docs' / 'research' /
                    '2026-10-10-weekly-watchlist.html').read_text()

    def test_required_universe_identity_and_crbs_block_are_present(self):
        for symbol in ('NVDA', 'MU', 'QCOM', 'PLTR', 'SPCX', 'CRBS',
                       'QBTS', 'RGTI', 'AVGO'):
            self.assertIn(symbol, self.text)
        self.assertIn('CRBS</td><td>Unresolved issuer / exchange / class',
                      self.text)
        self.assertIn('Blocked—do not substitute', self.text)

    def test_packet_separates_claim_types_and_states_missing_inputs(self):
        for label in ('Observation:', 'Hypothesis:', 'Missing data:',
                      'No verified holdings', 'No account-specific optimization',
                      'Premium income is not safe income',
                      'point-in-time availability', 'untouched holdout'):
            self.assertIn(label, self.text)
        self.assertGreaterEqual(self.text.count('https://'), 13)


if __name__ == '__main__':
    unittest.main()
