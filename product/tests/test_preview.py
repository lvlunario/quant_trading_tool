"""Static preview structure and isolation checks; not browser or financial QA."""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).resolve().parents[1] / 'preview/index.html').read_text()
        cls.page = Page(cls.text)

    def test_navigation_targets_exist_and_ids_are_unique(self):
        ids = [attrs['id'] for _, attrs in self.page.elements if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {'overview', 'portfolio', 'research', 'options', 'weekly'})
        for tag, attrs in self.page.elements:
            if tag == 'a' and attrs.get('href', '').startswith('#'):
                self.assertIn(attrs['href'][1:], ids)

    def test_no_scripts_forms_or_remote_assets(self):
        for tag, attrs in self.page.elements:
            self.assertNotIn(tag, {'script', 'form', 'input', 'iframe', 'object', 'embed'})
            for key, value in attrs.items():
                self.assertFalse(key.startswith('on'))
                if key in {'src', 'href'}:
                    self.assertFalse(value.startswith(('http:', 'https:', '//', 'javascript:')))
        self.assertIn("default-src 'none'", self.text)
        self.assertIn("form-action 'none'", self.text)

    def test_limitations_and_pending_acceptance_are_visible(self):
        for marker in ['Synthetic data only', 'Founder approval: pending',
                       'CRBS remains unresolved', 'Actionable option comparison blocked',
                       'not connected to the calculation kernel']:
            self.assertIn(marker, self.text)

    def test_disclosures_have_labels(self):
        tags = [tag for tag, _ in self.page.elements]
        self.assertEqual(tags.count('details'), 6)
        self.assertEqual(tags.count('summary'), tags.count('details'))
