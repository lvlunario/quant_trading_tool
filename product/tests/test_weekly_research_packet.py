"""The dated public research packet must remain complete and bounded."""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))


class WeeklyResearchPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = (Path(__file__).parents[1] / 'docs' / 'research' /
                    '2026-10-03-weekly-watchlist.html')
        cls.text = cls.path.read_text()
        cls.parser = _Parser()
        cls.parser.feed(cls.text)

    def test_required_watchlist_and_candidate_are_present(self):
        for symbol in ('NVDA', 'MU', 'QCOM', 'PLTR', 'SPCX', 'CRBS',
                       'QBTS', 'RGTI', 'AVGO'):
            self.assertIn(symbol, self.text)

    def test_packet_has_decision_frames_and_explicit_limits(self):
        for label in ('Actionability', 'Variant wedge', 'Why now',
                      'First rejection', 'What makes it investable',
                      'What kills it', 'Next workflow'):
            self.assertGreaterEqual(self.text.count(label), 9)
        for boundary in ('not a buy/sell list', 'No verified holdings',
                         'No option trade is actionable',
                         'Premium income is neither safe income'):
            self.assertIn(boundary, self.text)

    def test_packet_uses_primary_https_links_and_blocks_crbs(self):
        self.assertGreaterEqual(len(self.parser.links), 12)
        self.assertTrue(all(link.startswith('https://')
                            for link in self.parser.links))
        self.assertIn('CRBS — unresolved', self.text)
        self.assertIn('Retain as blocked in the security master', self.text)

