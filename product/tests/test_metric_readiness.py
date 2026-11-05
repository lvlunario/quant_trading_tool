from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from atlas.metrics import MetricDefinition, MetricValue
from atlas.metric_evidence import MetricPayload, assess_metric_input
from atlas.provenance import ObservationRecord
from atlas.reference import DataRightsRecord, SecurityRecord


class MetricReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        definition = MetricDefinition('MET_REVENUE', '1.0.0', 'Reported revenue',
            'money', 'USD', 'quarter', 'missing', 'reported@1.0.0')
        self.payload = MetricPayload(MetricValue(definition, Decimal('10')),
                                     date(2026, 4, 1), date(2026, 6, 30))
        self.observation = ObservationRecord('OBS_123456789ABC', 'SER_123456789ABC', 0,
            'INS_123456789ABC', 'PRV_12345678', 'DATA_12345678', 'MET_REVENUE',
            date(2026, 6, 30), self.now-timedelta(days=10), self.now-timedelta(days=9),
            'https://example.test/synthetic', 'a'*64, self.payload.payload_sha256, 'reported@1.0.0')
        self.security = SecurityRecord('INS_123456789ABC', 'ISS_123456789ABC',
            'Synthetic Issuer', 'Synthetic Class A', 'XNAS', 'USD', 'common_stock',
            'DEMO', date(2020, 1, 1), None, 'https://example.test/security', self.now)
        self.rights = DataRightsRecord('PRV_12345678', 'DATA_12345678', 'verified',
            ('internal_research',), 'https://example.test/terms', 'c'*64,
            self.now-timedelta(days=20), self.now+timedelta(days=20))

    def assess(self, **overrides):
        args = dict(payload=self.payload, observations=[self.observation],
            securities=[self.security], rights=[self.rights],
            series_id=self.observation.series_id, decision_at=self.now,
            use_case='internal_research', now=self.now)
        args.update(overrides)
        return assess_metric_input(**args)

    def assert_blocked(self, result, code):
        self.assertEqual(result.status, 'blocked')
        self.assertIn(code, result.codes)
        self.assertIsNone(result.payload)
        self.assertIsNone(result.observation_id)

    def test_valid_numeric_payload_is_released(self):
        result = self.assess()
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.payload.metric.value, Decimal('10'))
        self.assertEqual(result.observation_id, self.observation.observation_id)

    def test_dependencies_withhold_payload(self):
        for kwargs, code in (({'observations': []}, 'observation_unknown_series'),
                ({'securities': []}, 'identity_no_effective_instrument'),
                ({'rights': []}, 'rights_missing_evidence'),
                ({'use_case': 'customer_display'}, 'rights_use_not_permitted')):
            with self.subTest(code=code):
                self.assert_blocked(self.assess(**kwargs), code)

    def test_changed_numeric_value_is_blocked(self):
        payload = replace(self.payload, metric=replace(self.payload.metric, value=Decimal('11')))
        self.assert_blocked(self.assess(payload=payload), 'metric_payload_hash_mismatch')

    def test_bound_missing_value_is_still_blocked(self):
        payload = replace(self.payload, metric=replace(self.payload.metric,
                            value=None, missing_reason='missing_source'))
        observation = replace(self.observation, payload_sha256=payload.payload_sha256)
        self.assert_blocked(self.assess(payload=payload, observations=[observation]), 'metric_unavailable')

    def test_later_revision_cannot_supply_earlier_value(self):
        payload = replace(self.payload, metric=replace(self.payload.metric, value=Decimal('12')))
        revision = replace(self.observation, observation_id='OBS_ABCDEFGHIJKL', revision=1,
            available_at=self.now-timedelta(days=2), observed_at=self.now-timedelta(days=1),
            payload_sha256=payload.payload_sha256)
        self.assert_blocked(self.assess(payload=payload,
            observations=[self.observation, revision], decision_at=self.now-timedelta(days=5)),
            'metric_payload_hash_mismatch')
        self.assertEqual(self.assess(payload=payload,
            observations=[self.observation, revision]).payload.metric.value, Decimal('12'))

    def test_invalid_payload_raises(self):
        with self.assertRaisesRegex(ValueError, 'invalid_metric_payload'):
            self.assess(payload=None)
