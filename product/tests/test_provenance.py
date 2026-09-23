from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import unittest

from atlas.provenance import ObservationRecord, select_point_in_time


class PointInTimeProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 13, 11, tzinfo=timezone.utc)
        self.original = ObservationRecord(
            observation_id='OBS_123456789ABC', series_id='SER_123456789ABC', revision=0,
            instrument_id='INS_123456789ABC', provider_id='PRV_12345678',
            dataset_id='DATA_12345678', metric_id='MET_REVENUE_USD',
            as_of=date(2026, 6, 30),
            available_at=datetime(2026, 8, 1, 20, tzinfo=timezone.utc),
            observed_at=datetime(2026, 9, 1, 0, tzinfo=timezone.utc),
            source_uri='https://example.test/filing/original',
            source_sha256='a' * 64, payload_sha256='b' * 64,
            transform_version='atlas.fundamentals@1.0.0')
        self.revised = replace(
            self.original, observation_id='OBS_ABCDEFGHIJKL', revision=1,
            available_at=datetime(2026, 9, 10, 20, tzinfo=timezone.utc),
            observed_at=datetime(2026, 9, 11, 0, tzinfo=timezone.utc),
            source_uri='https://example.test/filing/revision',
            source_sha256='c' * 64, payload_sha256='d' * 64)

    def select(self, records, decision_at):
        return select_point_in_time(records, series_id='SER_123456789ABC',
                                    decision_at=decision_at, now=self.now)

    def test_revision_cannot_leak_into_earlier_decision(self):
        before_revision = self.select(
            [self.original, self.revised], datetime(2026, 9, 1, tzinfo=timezone.utc))
        after_revision = self.select(
            [self.original, self.revised], datetime(2026, 9, 12, tzinfo=timezone.utc))
        self.assertEqual((before_revision.observation_id, before_revision.revision),
                         ('OBS_123456789ABC', 0))
        self.assertEqual((after_revision.observation_id, after_revision.revision),
                         ('OBS_ABCDEFGHIJKL', 1))

    def test_not_yet_available_and_unknown_series_are_missing(self):
        unavailable = self.select(
            [self.original], datetime(2026, 7, 31, tzinfo=timezone.utc))
        unknown = select_point_in_time(
            [self.original], series_id='SER_UNKNOWNID1234', decision_at=self.now, now=self.now)
        self.assertEqual((unavailable.status, unavailable.code),
                         ('missing', 'not_yet_available'))
        self.assertEqual((unknown.status, unknown.code), ('missing', 'unknown_series'))

    def test_historical_availability_not_ingestion_time_drives_selection(self):
        result = self.select([self.original], datetime(2026, 8, 2, tzinfo=timezone.utc))
        self.assertEqual(result.status, 'selected')
        self.assertEqual(result.available_at, self.original.available_at)

    def test_future_observation_is_rejected(self):
        future = replace(self.original, observed_at=self.now + timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, 'future_observation'):
            self.select([future], self.now)

    def test_series_identity_conflict_is_rejected(self):
        conflict = replace(self.revised, metric_id='MET_FREE_CASH_FLOW')
        with self.assertRaisesRegex(ValueError, 'series_identity_conflict'):
            self.select([self.original, conflict], self.now)

    def test_duplicate_revision_and_backwards_revision_time_are_rejected(self):
        duplicate = replace(self.revised, revision=0)
        with self.assertRaisesRegex(ValueError, 'duplicate_revision'):
            self.select([self.original, duplicate], self.now)
        backwards = replace(self.revised,
                            available_at=self.original.available_at - timedelta(seconds=1),
                            observed_at=self.original.observed_at)
        with self.assertRaisesRegex(ValueError, 'revision_time_conflict'):
            self.select([self.original, backwards], self.now)

    def test_future_decision_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid_point_in_time_request'):
            self.select([self.original], self.now + timedelta(seconds=1))

    def test_invalid_record_fields_are_rejected(self):
        cases = ({'observation_id': None}, {'revision': True},
                 {'as_of': datetime(2026, 6, 30, tzinfo=timezone.utc)},
                 {'available_at': self.original.observed_at + timedelta(seconds=1)},
                 {'source_uri': 'http://example.test/source'},
                 {'source_sha256': 'short'}, {'payload_sha256': 'short'},
                 {'transform_version': 'latest'},
                 {'transform_version': 'atlas@1000000.1.1'})
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.original, **changes)
