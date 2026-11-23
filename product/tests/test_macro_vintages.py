from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from atlas.macro_vintages import (MacroReleaseRecord, assess_macro_input,
                                  select_macro_vintage)
from atlas.reference import DataRightsRecord


class MacroVintageTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 28, tzinfo=timezone.utc)
        self.initial = MacroReleaseRecord(
            'MREL_123456789ABC', 'MAC_123456789ABC', 'PRV_12345678',
            'DATA_12345678', 'Synthetic monthly index', 'index', 'monthly',
            'seasonally_adjusted', date(2026, 7, 1), date(2026, 7, 31), 0,
            datetime(2026, 8, 5, 12, 30, tzinfo=timezone.utc),
            datetime(2026, 8, 5, 13, tzinfo=timezone.utc), Decimal('100.0'), None,
            'https://example.test/macro/initial', 'a' * 64, 'macro.parse@1.0.0')
        self.revised = replace(
            self.initial, release_id='MREL_ABCDEFGHIJKL', revision=1,
            available_at=datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
            observed_at=datetime(2026, 9, 5, 13, tzinfo=timezone.utc),
            value=Decimal('99.5'), source_uri='https://example.test/macro/revised',
            source_sha256='b' * 64)
        self.rights = DataRightsRecord(
            'PRV_12345678', 'DATA_12345678', 'verified', ('internal_research',),
            'https://example.test/terms', 'c' * 64, self.now-timedelta(days=90),
            self.now+timedelta(days=90))

    def select(self, records, decision_at):
        return select_macro_vintage(
            records, macro_series_id=self.initial.macro_series_id,
            period_end=self.initial.period_end, decision_at=decision_at, now=self.now)

    def test_revision_cannot_leak_into_earlier_decision(self):
        early = self.select([self.initial, self.revised],
                            datetime(2026, 8, 20, tzinfo=timezone.utc))
        late = self.select([self.initial, self.revised], self.now)
        self.assertEqual((early.release_id, early.value),
                         (self.initial.release_id, Decimal('100.0')))
        self.assertEqual((late.release_id, late.value),
                         (self.revised.release_id, Decimal('99.5')))

    def test_not_yet_available_unknown_series_and_period_are_distinct(self):
        unavailable = self.select([self.initial],
                                  datetime(2026, 8, 1, tzinfo=timezone.utc))
        unknown_series = select_macro_vintage(
            [self.initial], macro_series_id='MAC_ABCDEFGHIJKL',
            period_end=self.initial.period_end, decision_at=self.now, now=self.now)
        unknown_period = select_macro_vintage(
            [self.initial], macro_series_id=self.initial.macro_series_id,
            period_end=date(2026, 6, 30), decision_at=self.now, now=self.now)
        self.assertEqual(unavailable.code, 'macro_not_yet_available')
        self.assertEqual(unknown_series.code, 'unknown_macro_series')
        self.assertEqual(unknown_period.code, 'unknown_macro_period')

    def test_rights_gate_controls_value_release(self):
        ready = assess_macro_input(
            [self.initial], [self.rights], macro_series_id=self.initial.macro_series_id,
            period_end=self.initial.period_end, decision_at=self.now,
            use_case='internal_research', now=self.now)
        blocked = assess_macro_input(
            [self.initial], [], macro_series_id=self.initial.macro_series_id,
            period_end=self.initial.period_end, decision_at=self.now,
            use_case='internal_research', now=self.now)
        self.assertEqual((ready.status, ready.value), ('ready', Decimal('100.0')))
        self.assertEqual(blocked.codes, ('rights_missing_evidence',))
        self.assertIsNone(blocked.value)

    def test_missing_value_is_not_coerced_to_zero(self):
        missing = replace(self.initial, value=None, missing_reason='source_missing')
        result = assess_macro_input(
            [missing], [self.rights], macro_series_id=missing.macro_series_id,
            period_end=missing.period_end, decision_at=self.now,
            use_case='internal_research', now=self.now)
        self.assertEqual(result.codes, ('macro_value_source_missing',))
        self.assertIsNone(result.value)

    def test_duplicate_or_backwards_revisions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_macro_revision'):
            self.select([self.initial, replace(self.revised, revision=0)], self.now)
        backwards = replace(self.revised,
            available_at=self.initial.available_at-timedelta(seconds=1),
            observed_at=self.initial.observed_at)
        with self.assertRaisesRegex(ValueError, 'macro_revision_time_conflict'):
            self.select([self.initial, backwards], self.now)

    def test_series_identity_conflict_is_rejected(self):
        conflict = replace(self.revised, unit='percent')
        with self.assertRaisesRegex(ValueError, 'macro_series_identity_conflict'):
            self.select([self.initial, conflict], self.now)

    def test_future_observation_and_future_decision_are_rejected(self):
        future = replace(self.initial, observed_at=self.now+timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, 'future_macro_observation'):
            self.select([future], self.now)
        with self.assertRaisesRegex(ValueError, 'invalid_macro_selection_request'):
            self.select([self.initial], self.now+timedelta(seconds=1))

    def test_invalid_release_fields_are_rejected(self):
        cases = (
            {'release_id': 'bad'}, {'macro_series_id': 'INS_123456789ABC'},
            {'revision': True}, {'frequency': 'random'},
            {'value': Decimal('NaN')}, {'value': Decimal('0'), 'missing_reason': 'suppressed'},
            {'value': None, 'missing_reason': None}, {'source_uri': 'http://example.test'},
            {'source_sha256': 'short'}, {'transform_version': 'latest'},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.initial, **changes)


if __name__ == '__main__':
    unittest.main()
