"""Current public watchlist identities remain exact, dated and fail closed."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.watchlist_registry import load_public_watchlist_registry


class WatchlistRegistryTests(unittest.TestCase):
    def setUp(self):
        self.path = (Path(__file__).parents[1] / 'fixtures' /
                     'public-watchlist-identities.json')
        self.raw = self.path.read_bytes()
        self.now = datetime(2026, 10, 3, 1, tzinfo=timezone.utc)

    def payload(self):
        return json.loads(self.raw)

    def test_current_universe_resolves_and_crbs_stays_blocked(self):
        registry = load_public_watchlist_registry(self.raw, now=self.now)
        summary = registry.public_summary()
        self.assertEqual(summary['resolved_count'], 8)
        self.assertEqual(summary['blocked'], [{
            'symbol': 'CRBS', 'code': 'unresolved_no_authoritative_match'}])
        self.assertEqual(set(summary['resolved_symbols']),
                         {'NVDA', 'MU', 'QCOM', 'PLTR', 'SPCX',
                          'QBTS', 'RGTI', 'AVGO'})
        self.assertIn('no prices', summary['readiness'])

    def test_universe_cannot_omit_duplicate_or_promote_crbs(self):
        for mutate in (
                lambda value: value['records'].pop(),
                lambda value: value['records'].append(deepcopy(value['records'][0])),
                lambda value: value['blocked'].__setitem__(0, {
                    **value['blocked'][0], 'symbol': 'CRBG'})):
            payload = self.payload()
            mutate(payload)
            with self.subTest(payload=payload), self.assertRaises(
                    ValueError, msg='universe mutation must fail'):
                load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)

    def test_unknown_fields_and_unapproved_sources_fail(self):
        payload = self.payload()
        payload['records'][0]['price'] = '0'
        with self.assertRaisesRegex(ValueError, 'invalid_watchlist_record_schema'):
            load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)
        payload = self.payload()
        payload['records'][0]['source_uri'] = 'https://example.test/nvda'
        with self.assertRaisesRegex(ValueError, 'unapproved_identity_source'):
            load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)

    def test_future_or_mixed_observation_times_fail(self):
        payload = self.payload()
        payload['as_of'] = '2026-10-04T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'unsupported_watchlist_registry'):
            load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)
        payload = self.payload()
        payload['records'][0]['observed_at'] = '2026-10-02T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'inconsistent_watchlist_record'):
            load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)

    def test_overlap_and_identity_conflict_fail_closed(self):
        payload = self.payload()
        duplicate = deepcopy(payload['records'][0])
        duplicate['instrument_id'] = 'INS_WATCH2026100399'
        payload['records'].append(duplicate)
        payload['blocked'][0]['symbol'] = 'RGTI'
        with self.assertRaises(ValueError):
            load_public_watchlist_registry(json.dumps(payload).encode(), now=self.now)

    def test_invalid_bytes_and_oversize_are_rejected(self):
        for raw in (b'', b'not-json', b'\xff', b'{' + b'x' * 65_536):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                load_public_watchlist_registry(raw, now=self.now)

