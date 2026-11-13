"""Public source candidates must not become usable metrics by implication."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from atlas.source_catalog import load_public_source_catalog
from atlas.watchlist_registry import load_public_watchlist_registry


class PublicSourceCatalogTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.raw = (fixtures / 'public-research-sources.json').read_bytes()
        self.now = datetime(2026, 10, 3, 1, tzinfo=timezone.utc)
        self.registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(), now=self.now)

    def payload(self):
        return json.loads(self.raw)

    def test_eight_resolved_sources_are_catalogued_but_blocked(self):
        catalog = load_public_source_catalog(self.raw, self.registry, now=self.now)
        summary = catalog.public_summary()
        self.assertEqual(summary['candidate_count'], 8)
        self.assertEqual([item['symbol'] for item in summary['items']],
                         ['NVDA', 'MU', 'AVGO', 'QCOM', 'PLTR', 'SPCX',
                          'QBTS', 'RGTI'])
        for item in summary['items']:
            self.assertEqual(item['identity_status'], 'resolved')
            self.assertEqual(item['metric_status'], 'unavailable')
            self.assertEqual(item['decision'],
                             'blocked_pending_rights_and_extraction')
        self.assertIn('no retrieved bytes', summary['readiness'])

    def test_each_candidate_uses_its_expected_official_issuer_host(self):
        catalog = load_public_source_catalog(self.raw, self.registry, now=self.now)
        expected = {
            'NVDA': 'nvidianews.nvidia.com',
            'MU': 'investors.micron.com',
            'AVGO': 'investors.broadcom.com',
            'QCOM': 'investor.qualcomm.com',
            'PLTR': 'investors.palantir.com',
            'SPCX': 'ir.spacex.com',
            'QBTS': 'ir.dwavequantum.com',
            'RGTI': 'investors.rigetti.com',
        }
        self.assertEqual(
            {item.symbol: urlsplit(item.source_uri).hostname
             for item in catalog.candidates}, expected)

    def test_metric_value_or_unknown_field_cannot_enter_catalog(self):
        payload = self.payload()
        payload['sources'][0]['metric_value'] = '96.2'
        with self.assertRaisesRegex(ValueError, 'invalid_source_candidate_schema'):
            load_public_source_catalog(json.dumps(payload).encode(), self.registry,
                                       now=self.now)

    def test_instrument_identity_must_match_registry(self):
        payload = self.payload()
        payload['sources'][0]['instrument_id'] = 'INS_WATCH2026100302'
        with self.assertRaisesRegex(ValueError, 'source_candidate_identity_mismatch'):
            load_public_source_catalog(json.dumps(payload).encode(), self.registry,
                                       now=self.now)

    def test_unapproved_domain_or_promoted_state_fails(self):
        for change in (
                {'source_uri': 'https://example.test/release'},
                {'rights_state': 'verified'},
                {'extraction_state': 'complete'}):
            payload = self.payload()
            payload['sources'][0].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, 'invalid_source_candidate'):
                load_public_source_catalog(json.dumps(payload).encode(), self.registry,
                                           now=self.now)

    def test_future_or_mixed_cutoff_fails(self):
        payload = self.payload()
        payload['sources'][0]['published_on'] = '2026-10-04'
        with self.assertRaisesRegex(ValueError, 'invalid_source_candidate'):
            load_public_source_catalog(json.dumps(payload).encode(), self.registry,
                                       now=self.now)
        payload = self.payload()
        payload['as_of'] = '2026-10-02T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'unsupported_source_catalog'):
            load_public_source_catalog(json.dumps(payload).encode(), self.registry,
                                       now=self.now)

    def test_missing_reordered_duplicate_and_invalid_bytes_fail(self):
        variants = []
        payload = self.payload(); payload['sources'].pop(); variants.append(json.dumps(payload).encode())
        payload = self.payload(); payload['sources'].reverse(); variants.append(json.dumps(payload).encode())
        payload = self.payload(); payload['sources'][1]['document_id'] = payload['sources'][0]['document_id']; variants.append(json.dumps(payload).encode())
        variants.extend((b'', b'not-json', b'\xff', b'{' + b'x' * 65_536))
        for raw in variants:
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                load_public_source_catalog(raw, self.registry, now=self.now)
