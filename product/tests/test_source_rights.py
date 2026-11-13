"""Source review tracking cannot imply rights or enable retrieval."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.source_catalog import load_public_source_catalog
from atlas.source_rights import load_source_rights_manifest
from atlas.watchlist_registry import load_public_watchlist_registry


class SourceRightsManifestTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parents[1] / 'fixtures'
        self.raw = (fixtures / 'public-source-rights-review.json').read_bytes()
        self.now = datetime(2026, 10, 4, 1, tzinfo=timezone.utc)
        registry = load_public_watchlist_registry(
            (fixtures / 'public-watchlist-identities.json').read_bytes(), now=self.now)
        self.catalog = load_public_source_catalog(
            (fixtures / 'public-research-sources.json').read_bytes(), registry,
            now=self.now)

    def payload(self):
        return json.loads(self.raw)

    def test_unreviewed_sources_remain_blocked_by_policy(self):
        manifest = load_source_rights_manifest(
            self.raw, self.catalog, now=self.now)
        summary = manifest.public_summary()
        self.assertEqual((summary['status'], summary['review_count']), ('blocked', 8))
        self.assertEqual([item['symbol'] for item in summary['items']],
                         ['NVDA', 'MU', 'AVGO', 'QCOM', 'PLTR', 'SPCX',
                          'QBTS', 'RGTI'])
        for item in summary['items']:
            self.assertEqual(item['rights_status'], 'not_started')
            self.assertEqual(item['retrieval_status'], 'blocked')
            self.assertEqual(item['decision'], 'terms_evidence_required')
        self.assertFalse(summary['retrieval_policy']['network_fetch_enabled'])
        self.assertFalse(summary['retrieval_policy']['retain_source_bytes'])

    def test_review_cannot_be_promoted_without_evidence_schema(self):
        for changes in (
                {'review_state': 'verified'},
                {'terms_uri': 'https://example.test/terms'},
                {'evidence_sha256': 'a' * 64},
                {'reviewed_at': '2026-10-04T00:00:00+00:00'}):
            payload = self.payload()
            payload['reviews'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(
                    ValueError, 'unsubstantiated_source_rights_review'):
                load_source_rights_manifest(
                    json.dumps(payload).encode(), self.catalog, now=self.now)

    def test_retrieval_policy_cannot_be_relaxed(self):
        unsafe = (
            ('network_fetch_enabled', True),
            ('follow_redirects', True),
            ('retain_source_bytes', True),
            ('max_source_bytes', 10 * 1024 * 1024),
            ('allowed_content_types', ['text/html', 'application/octet-stream']),
        )
        for field, value in unsafe:
            payload = self.payload()
            payload['retrieval_policy'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, 'unsafe_retrieval_policy'):
                load_source_rights_manifest(
                    json.dumps(payload).encode(), self.catalog, now=self.now)

    def test_review_universe_must_exactly_match_catalog(self):
        variants = []
        payload = self.payload(); payload['reviews'].pop(); variants.append(payload)
        payload = self.payload(); payload['reviews'].reverse(); variants.append(payload)
        payload = self.payload(); payload['reviews'][0]['symbol'] = 'MU'; variants.append(payload)
        payload = self.payload(); payload['reviews'][0]['document_id'] = 'DOC_OTHER2026100401'; variants.append(payload)
        for payload in variants:
            with self.subTest(payload=payload), self.assertRaisesRegex(
                    ValueError, 'source_rights_catalog_mismatch'):
                load_source_rights_manifest(
                    json.dumps(payload).encode(), self.catalog, now=self.now)

    def test_cutoff_use_case_and_unknown_fields_fail_closed(self):
        variants = []
        payload = self.payload(); payload['assessed_at'] = '2026-10-05T00:00:00+00:00'; variants.append(payload)
        payload = self.payload(); payload['assessed_at'] = '2026-10-02T00:00:00+00:00'; variants.append(payload)
        payload = self.payload(); payload['use_case'] = 'redistribution'; variants.append(payload)
        payload = self.payload(); payload['reviews'][0]['reviewer'] = 'invented'; variants.append(payload)
        for payload in variants:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                load_source_rights_manifest(
                    json.dumps(payload).encode(), self.catalog, now=self.now)

    def test_invalid_bytes_and_operands_are_rejected(self):
        for raw in (b'', b'not-json', b'\xff', b'{' + b'x' * 65_536):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                load_source_rights_manifest(raw, self.catalog, now=self.now)
        with self.assertRaisesRegex(ValueError, 'invalid_source_rights_catalog'):
            load_source_rights_manifest(self.raw, object(), now=self.now)
