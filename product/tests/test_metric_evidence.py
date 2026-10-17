from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
import unittest

from atlas.metrics import MetricDefinition, MetricValue
from atlas.metric_evidence import MetricPayload, verify_metric_binding
from atlas.provenance import ObservationRecord, select_point_in_time


class MetricEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.definition = MetricDefinition('MET_REVENUE', '1.0.0', 'Reported revenue',
            'money', 'USD', 'quarter', 'missing', 'reported@1.0.0')
        self.payload = MetricPayload(MetricValue(self.definition, Decimal('123.40')),
                                     date(2026, 4, 1), date(2026, 6, 30))
        self.observation = ObservationRecord('OBS_123456789ABC', 'SER_123456789ABC', 0,
            'INS_123456789ABC', 'PRV_12345678', 'DATA_12345678', 'MET_REVENUE',
            date(2026, 6, 30), datetime(2026, 8, 1, tzinfo=timezone.utc),
            datetime(2026, 9, 1, tzinfo=timezone.utc), 'https://example.test/synthetic',
            'a' * 64, self.payload.payload_sha256, 'reported@1.0.0')

    def test_canonical_bytes_are_independently_specified(self):
        expected = (b'{"definition":{"currency":"USD","definition_version":"1.0.0",'
            b'"formula":"Reported revenue","metric_id":"MET_REVENUE","null_policy":"missing",'
            b'"period":"quarter","transform_version":"reported@1.0.0","unit":"money"},'
            b'"missing_reason":null,"period_end":"2026-06-30","period_start":"2026-04-01",'
            b'"schema_version":1,"value":"123.40"}')
        self.assertEqual(self.payload.canonical_bytes(), expected)
        self.assertEqual(self.payload.payload_sha256, sha256(expected).hexdigest())
        verify_metric_binding(self.payload, self.observation)

    def test_value_definition_and_period_changes_break_hash(self):
        variants = [replace(self.payload, metric=MetricValue(self.definition, Decimal('124'))),
            replace(self.payload, period_start=date(2026, 4, 2)),
            replace(self.payload, metric=MetricValue(replace(self.definition,
                definition_version='2.0.0'), Decimal('123.40')))]
        for payload in variants:
            with self.assertRaisesRegex(ValueError, 'metric_payload_hash_mismatch'):
                verify_metric_binding(payload, self.observation)

    def test_metadata_mismatches_fail_closed(self):
        for field, value, code in (
            ('metric_id', 'MET_OTHER', 'metric_identity_mismatch'),
            ('transform_version', 'reported@2.0.0', 'metric_transform_mismatch'),
            ('as_of', date(2026, 6, 29), 'metric_as_of_mismatch'),
            ('payload_sha256', 'b' * 64, 'metric_payload_hash_mismatch')):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, code):
                verify_metric_binding(self.payload, replace(self.observation, **{field: value}))

    def test_missing_and_zero_have_different_hashes(self):
        missing = replace(self.payload, metric=MetricValue(self.definition, None, 'missing_source'))
        zero = replace(self.payload, metric=MetricValue(self.definition, Decimal('0')))
        self.assertNotEqual(missing.payload_sha256, zero.payload_sha256)
        verify_metric_binding(missing, replace(self.observation, payload_sha256=missing.payload_sha256))

    def test_invalid_periods_and_operands_rejected(self):
        for changes in ({'period_start': date(2026, 7, 1)}, {'period_end': None},
                        {'period_start': datetime(2026, 4, 1)}, {'metric': None}):
            with self.assertRaises(ValueError):
                replace(self.payload, **changes)
        with self.assertRaises(ValueError):
            verify_metric_binding(None, self.observation)

    def test_instant_period_is_one_date(self):
        metric = MetricValue(replace(self.definition, period='instant'), Decimal('1'))
        MetricPayload(metric, date(2026, 6, 30), date(2026, 6, 30))
        with self.assertRaises(ValueError):
            replace(self.payload, metric=metric)

    def test_revision_selection_retains_original_value_binding(self):
        revised_payload = replace(self.payload, metric=MetricValue(self.definition, Decimal('125')))
        revised = replace(self.observation, observation_id='OBS_ABCDEFGHIJKL', revision=1,
            available_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            observed_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            payload_sha256=revised_payload.payload_sha256)
        selected = select_point_in_time([self.observation, revised],
            series_id=self.observation.series_id,
            decision_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
            now=datetime(2026, 9, 16, tzinfo=timezone.utc))
        self.assertEqual(selected.payload_sha256, self.payload.payload_sha256)
        with self.assertRaises(ValueError):
            verify_metric_binding(revised_payload, self.observation)
