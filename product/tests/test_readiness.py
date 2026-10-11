from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import unittest

from atlas.provenance import ObservationRecord, assess_research_input
from atlas.reference import DataRightsRecord, SecurityRecord


class ResearchReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 14, 0, tzinfo=timezone.utc)
        self.observation = ObservationRecord(
            'OBS_123456789ABC', 'SER_123456789ABC', 0, 'INS_123456789ABC',
            'PRV_12345678', 'DATA_12345678', 'MET_REVENUE_USD', date(2026, 6, 30),
            self.now - timedelta(days=3), self.now - timedelta(days=2),
            'https://example.test/source', 'a' * 64, 'b' * 64,
            'atlas.fundamentals@1.0.0')
        self.security = SecurityRecord(
            'INS_123456789ABC', 'ISS_123456789ABC', 'Synthetic Issuer',
            'Synthetic Class A', 'XNAS', 'USD', 'common_stock', 'DEMO',
            date(2020, 1, 1), None, 'https://example.test/security',
            self.now - timedelta(days=1))
        self.rights = DataRightsRecord(
            'PRV_12345678', 'DATA_12345678', 'verified', ('internal_research',),
            'https://example.test/terms', 'c' * 64, self.now - timedelta(days=10),
            self.now + timedelta(days=30))

    def assess(self, observations=None, securities=None, rights=None,
               use_case='internal_research'):
        return assess_research_input(
            ([self.observation] if observations is None else observations),
            [self.security] if securities is None else securities,
            [self.rights] if rights is None else rights,
            series_id='SER_123456789ABC', decision_at=self.now,
            use_case=use_case, now=self.now)

    def test_all_three_gates_produce_ready_input(self):
        result = self.assess()
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.observation_id, self.observation.observation_id)
        self.assertEqual(result.payload_sha256, self.observation.payload_sha256)

    def test_missing_observation_blocks_without_payload(self):
        result = self.assess(observations=[])
        self.assertEqual(result.codes, ('observation_unknown_series',))
        self.assertIsNone(result.payload_sha256)

    def test_missing_effective_identity_blocks(self):
        result = self.assess(securities=[])
        self.assertEqual(result.codes, ('identity_no_effective_instrument',))
        self.assertIsNone(result.observation_id)

    def test_missing_rights_blocks(self):
        result = self.assess(rights=[])
        self.assertEqual(result.codes, ('rights_missing_evidence',))

    def test_nonpermitted_use_blocks(self):
        result = self.assess(use_case='customer_display')
        self.assertEqual(result.codes, ('rights_use_not_permitted',))

    def test_all_failed_dependencies_are_reported(self):
        result = self.assess(securities=[], rights=[])
        self.assertEqual(result.codes, ('identity_no_effective_instrument',
                                        'rights_missing_evidence'))

    def test_expired_rights_block(self):
        expired = replace(self.rights, valid_until=self.now)
        self.assertEqual(self.assess(rights=[expired]).codes,
                         ('rights_expired_evidence',))
