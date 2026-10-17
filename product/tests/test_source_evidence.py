from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from atlas.metric_evidence import (MetricPayload, assess_sourced_metric_input)
from atlas.metrics import MetricDefinition, MetricValue
from atlas.provenance import ObservationRecord
from atlas.reference import DataRightsRecord, SecurityRecord
from atlas.source_evidence import ResearchSourceRecord, assess_source_binding


class ResearchSourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 28, tzinfo=timezone.utc)
        self.available_at = self.now - timedelta(days=10)
        self.retrieved_at = self.now - timedelta(days=9)
        definition = MetricDefinition('MET_REVENUE', '1.0.0', 'Reported revenue',
            'money', 'USD', 'quarter', 'missing', 'reported@1.0.0')
        self.payload = MetricPayload(MetricValue(definition, Decimal('10')),
                                     date(2026, 4, 1), date(2026, 6, 30))
        self.source = ResearchSourceRecord(
            'DOC_123456789ABC', 'INS_123456789ABC', 'PRV_12345678',
            'DATA_12345678', 'regulator_filing', 'application/pdf',
            self.available_at - timedelta(minutes=1), self.available_at,
            self.retrieved_at, 'https://example.test/filing', 'a' * 64)
        self.observation = ObservationRecord(
            'OBS_123456789ABC', 'SER_123456789ABC', 0,
            self.source.instrument_id, self.source.provider_id, self.source.dataset_id,
            'MET_REVENUE', date(2026, 6, 30), self.source.available_at,
            self.source.retrieved_at, self.source.source_uri, self.source.source_sha256,
            self.payload.payload_sha256, 'reported@1.0.0')
        self.security = SecurityRecord(
            self.source.instrument_id, 'ISS_123456789ABC', 'Synthetic Issuer',
            'Synthetic Class A', 'XNAS', 'USD', 'common_stock', 'DEMO',
            date(2020, 1, 1), None, 'https://example.test/security', self.retrieved_at)
        self.rights = DataRightsRecord(
            self.source.provider_id, self.source.dataset_id, 'verified',
            ('internal_research',), 'https://example.test/terms', 'c' * 64,
            self.now - timedelta(days=20), self.now + timedelta(days=20))

    def assess_metric(self, source=None, observations=None):
        return assess_sourced_metric_input(
            self.payload, [self.observation] if observations is None else observations,
            [self.security], [self.rights], self.source if source is None else source,
            series_id=self.observation.series_id, decision_at=self.now,
            use_case='internal_research', now=self.now)

    def test_exact_source_binding_releases_metric(self):
        binding = assess_source_binding(self.source, self.observation, now=self.now)
        self.assertEqual(binding.status, 'ready')
        self.assertEqual(binding.document_id, self.source.document_id)
        result = self.assess_metric()
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.payload.metric.value, Decimal('10'))

    def test_identity_mismatches_fail_closed(self):
        cases = (
            ('instrument_id', 'INS_ABCDEFGHIJKL', 'source_instrument_mismatch'),
            ('provider_id', 'PRV_ABCDEFGH', 'source_provider_mismatch'),
            ('dataset_id', 'DATA_ABCDEFGH', 'source_dataset_mismatch'),
        )
        for field, value, code in cases:
            with self.subTest(code=code):
                result = self.assess_metric(source=replace(self.source, **{field: value}))
                self.assertEqual(result.status, 'blocked')
                self.assertIn(code, result.codes)
                self.assertIsNone(result.payload)

    def test_exact_uri_and_hash_are_required(self):
        for changes, code in (({'source_uri': 'https://example.test/other'},
                               'source_uri_mismatch'),
                              ({'source_sha256': 'b' * 64}, 'source_hash_mismatch')):
            with self.subTest(code=code):
                self.assertIn(code, self.assess_metric(
                    source=replace(self.source, **changes)).codes)

    def test_availability_and_retrieval_order_are_bound(self):
        shifted = replace(self.source,
                          available_at=self.source.available_at + timedelta(seconds=1))
        self.assertIn('source_availability_mismatch', self.assess_metric(source=shifted).codes)
        late_observation = replace(self.observation,
                                   observed_at=self.source.retrieved_at - timedelta(seconds=1))
        result = self.assess_metric(observations=[late_observation])
        self.assertIn('source_retrieved_after_observation', result.codes)

    def test_future_retrieval_is_blocked(self):
        future = replace(self.source,
            published_at=self.now + timedelta(seconds=1),
            available_at=self.now + timedelta(seconds=2),
            retrieved_at=self.now + timedelta(seconds=3))
        result = assess_source_binding(future, self.observation, now=self.now)
        self.assertEqual(result.codes, ('source_future_retrieval',))

    def test_invalid_source_contract_is_rejected(self):
        cases = (
            {'document_id': 'bad'}, {'source_kind': 'social_post'},
            {'content_type': 'application/octet-stream'},
            {'source_uri': 'http://example.test/filing'},
            {'source_sha256': 'short'},
            {'available_at': self.source.published_at - timedelta(seconds=1)},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.source, **changes)

    def test_existing_metric_failures_remain_authoritative(self):
        changed = replace(self.payload,
            metric=replace(self.payload.metric, value=Decimal('11')))
        result = assess_sourced_metric_input(
            changed, [self.observation], [self.security], [self.rights], self.source,
            series_id=self.observation.series_id, decision_at=self.now,
            use_case='internal_research', now=self.now)
        self.assertEqual(result.codes, ('metric_payload_hash_mismatch',))


if __name__ == '__main__':
    unittest.main()
