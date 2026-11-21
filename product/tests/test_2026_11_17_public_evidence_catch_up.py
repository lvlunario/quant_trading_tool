"""November 17 public-evidence catch-up remains dated and fail-closed."""
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


class NovemberSeventeenEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = (Path(__file__).parents[1] / "docs" / "research" /
                "2026-11-17-public-evidence-catch-up.html")
        cls.text = path.read_text()
        cls.parser = _Links()
        cls.parser.feed(cls.text)

    def test_packet_is_separately_dated_and_not_backdated(self):
        self.assertIn('data-evidence-cut="2026-11-17T19:10:00+08:00"',
                      self.text)
        self.assertIn("actual preparation date", self.text)
        self.assertIn("not a backdated November 14 packet", self.text)

    def test_universe_identity_and_crbs_block_are_explicit(self):
        for symbol in ("NVDA", "MU", "QCOM", "PLTR", "SPCX", "CRBS",
                       "QBTS", "RGTI", "AMD", "AVGO"):
            self.assertIn(symbol, self.text)
        self.assertIn("CRBS remains unresolved", self.text)
        self.assertIn("Cerebras Systems under", self.text)
        self.assertIn("CBRS, not CRBS", self.text)
        self.assertIn("Any CBRS, CRBU or BRBS substitution", self.text)

    def test_fresh_macro_and_event_cutoffs_are_locked(self):
        for marker in ("October CPI", "+0.4%", "October PPI", "+6.5%",
                       "4.83% / 5.12%", "year-over-year CPI changes",
                       "after this Manila evidence cut", "$4.5M",
                       "$1.4M"):
            self.assertIn(marker, self.text)

    def test_claim_types_and_decision_limits_stay_separate(self):
        for marker in ("Observation.", "Hypothesis.", "Missing data.",
                       "not a buy/sell list", "No verified holdings",
                       "no option trade is actionable",
                       "Premium income is not safe income",
                       "untouched holdout"):
            self.assertIn(marker, self.text)
        self.assertGreaterEqual(len(self.parser.links), 24)
        self.assertTrue(all(link.startswith("https://")
                            for link in self.parser.links))


if __name__ == "__main__":
    unittest.main()
