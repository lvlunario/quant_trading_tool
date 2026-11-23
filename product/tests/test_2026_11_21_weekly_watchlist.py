"""November 21 public research stays source-bound and decision-safe."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import unittest


class _PacketParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self.links.append(attributes.get("href", ""))
        if tag == "script":
            self.scripts += 1


class NovemberTwentyOneWatchlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = (Path(__file__).parents[1] / "docs" / "research" /
                    "2026-11-21-weekly-watchlist.html")
        cls.text = cls.path.read_text()
        cls.parser = _PacketParser()
        cls.parser.feed(cls.text)

    def test_cutoff_and_required_universe_are_explicit(self):
        self.assertIn('data-evidence-cut="2026-11-21T19:46:00+08:00"',
                      self.text)
        self.assertIn("November 21, 2026, 19:46 Asia/Manila", self.text)
        for symbol in ("NVDA", "MU", "QCOM", "PLTR", "SPCX", "CRBS",
                       "QBTS", "RGTI", "AMD", "AVGO"):
            self.assertIn(symbol, self.text)

    def test_identity_control_blocks_crbs_without_substitution(self):
        self.assertIn("CRBS remains identity-blocked", self.text)
        self.assertIn("CBRS does not permit substitution", self.text)
        self.assertIn("QBTS</td><td>D-Wave Quantum Inc.", self.text)
        self.assertIn("Nasdaq Stock Market LLC · common stock", self.text)
        self.assertIn("Nasdaq Capital Market · common stock", self.text)

    def test_observations_hypotheses_and_missing_data_stay_separate(self):
        for marker in ("Observation.", "Hypothesis.",
                       "Missing data / falsifier.",
                       "Missing data / first rejection"):
            self.assertIn(marker, self.text)
        for label in ("Actionability", "Variant wedge", "Why now",
                      "First rejection", "What supports it", "What kills it",
                      "Next workflow"):
            self.assertGreaterEqual(self.text.count(label), 4)

    def test_fresh_macro_and_issuer_events_are_preserved(self):
        for evidence in ("October CPI", "October PPI", "4.63% / 4.92%",
                         "3.75%–4.00%", "$115.8B", "$107.6B",
                         "December 9", "December 17"):
            self.assertIn(evidence, self.text)
        self.assertIn("no award funds had been received by September 30",
                      self.text)
        self.assertIn("two putative class actions and a derivative action",
                      self.text)

    def test_research_and_portfolio_boundaries_are_explicit(self):
        for boundary in ("No verified holdings", "licensed current prices",
                         "consensus estimates", "live option chains",
                         "reconciled collateral", "No option trade is actionable",
                         "point-in-time prices", "costs, execution delay",
                         "aligned benchmark", "untouched holdout",
                         "Premium income is not safe income"):
            self.assertIn(boundary, self.text)

    def test_packet_is_self_contained_and_uses_https_primary_sources(self):
        self.assertEqual(self.parser.scripts, 0)
        self.assertGreaterEqual(len(self.parser.links), 30)
        self.assertTrue(all(link.startswith("https://")
                            for link in self.parser.links))
        forbidden_hosts = {"wikipedia.org", "reuters.com", "bloomberg.com",
                           "finance.yahoo.com"}
        self.assertFalse({urlparse(link).hostname for link in self.parser.links}
                         & forbidden_hosts)


if __name__ == "__main__":
    unittest.main()
