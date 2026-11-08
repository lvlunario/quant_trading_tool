"""November 7 public watchlist delta remains complete and bounded."""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href", ""))


class NovemberSevenWatchlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = (Path(__file__).parents[1] / "docs" / "research" /
                "2026-11-07-weekly-watchlist.html")
        cls.text = path.read_text()
        cls.parser = _Links()
        cls.parser.feed(cls.text)

    def test_required_universe_and_supported_additions_are_present(self):
        for symbol in ("NVDA", "MU", "QCOM", "PLTR", "SPCX", "CRBS",
                       "QBTS", "RGTI", "AMD", "AVGO"):
            self.assertIn(symbol, self.text)

    def test_identity_correction_and_crbs_block_are_explicit(self):
        self.assertIn("QBTS is Nasdaq common stock", self.text)
        self.assertIn("corrects the Oct. 31 report's NYSE label", self.text)
        self.assertIn("CRBS remains unresolved", self.text)
        self.assertIn("do not substitute CBRS, CRBU or BRBS", self.text)

    def test_claim_types_and_decision_boundaries_stay_separate(self):
        for marker in ("Observation.", "Hypothesis.", "Missing data.",
                       "not a buy/sell list", "No verified holdings",
                       "no option trade is actionable",
                       "Premium income is not safe income",
                       "point-in-time inputs", "untouched holdout"):
            self.assertIn(marker, self.text)

    def test_top_cards_include_pm_research_fields_and_primary_links(self):
        for label in ("Actionability", "Variant wedge", "Why now",
                      "First rejection", "What makes it investable",
                      "What kills it", "Next workflow"):
            self.assertGreaterEqual(self.text.count(label), 4)
        self.assertGreaterEqual(len(self.parser.links), 25)
        self.assertTrue(all(link.startswith("https://")
                            for link in self.parser.links))


if __name__ == "__main__":
    unittest.main()
