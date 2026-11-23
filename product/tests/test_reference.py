from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import unittest

from atlas.reference import (DataRightsRecord, SecurityRecord, check_data_rights,
                             resolve_security, verify_instrument)


class SecurityMasterTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 13, 7, tzinfo=timezone.utc)
        self.record = SecurityRecord(
            instrument_id='INS_123456789ABC', issuer_id='ISS_123456789ABC',
            issuer_name='Synthetic Issuer',
            security_name='Synthetic Class A', exchange_mic='XNAS', currency='USD',
            security_class='common_stock', symbol='DEMO', effective_from=date(2025, 1, 1),
            effective_to=None, source_uri='https://example.test/security/DEMO',
            observed_at=self.now)

    def test_effective_identity_resolves(self):
        result = resolve_security([self.record], symbol='DEMO', exchange_mic='XNAS',
                                  on_date=date(2026, 9, 13), now=self.now)
        self.assertEqual((result.status, result.instrument_id),
                         ('resolved', 'INS_123456789ABC'))

    def test_symbol_reuse_resolves_by_effective_date(self):
        old = replace(self.record, instrument_id='INS_OLDIDENTITY01',
                      effective_to=date(2026, 1, 1))
        new = replace(self.record, instrument_id='INS_NEWIDENTITY01',
                      issuer_name='New Synthetic Issuer', security_name='New Synthetic Class A',
                      effective_from=date(2026, 1, 1))
        before = resolve_security([old, new], symbol='DEMO', exchange_mic='XNAS',
                                  on_date=date(2025, 12, 31), now=self.now)
        after = resolve_security([old, new], symbol='DEMO', exchange_mic='XNAS',
                                 on_date=date(2026, 1, 1), now=self.now)
        self.assertEqual(before.instrument_id, 'INS_OLDIDENTITY01')
        self.assertEqual(after.instrument_id, 'INS_NEWIDENTITY01')

    def test_overlapping_identities_are_ambiguous(self):
        conflict = replace(self.record, instrument_id='INS_OTHERIDENTITY1')
        result = resolve_security([self.record, conflict], symbol='DEMO', exchange_mic='XNAS',
                                  on_date=date(2026, 9, 13), now=self.now)
        self.assertEqual((result.status, result.code), ('ambiguous', 'overlapping_identities'))

    def test_missing_symbol_is_not_guessed(self):
        result = resolve_security([], symbol='CRBS', exchange_mic='XNAS',
                                  on_date=date(2026, 9, 13), now=self.now)
        self.assertEqual((result.status, result.instrument_id), ('missing', None))

    def test_conflicting_attributes_and_future_evidence_fail(self):
        conflict = replace(self.record, issuer_id='ISS_DIFFERENTID01')
        with self.assertRaisesRegex(ValueError, 'instrument_identity_conflict'):
            resolve_security([self.record, conflict], symbol='DEMO', exchange_mic='XNAS',
                             on_date=date(2026, 9, 13), now=self.now)
        with self.assertRaisesRegex(ValueError, 'future_security_evidence'):
            resolve_security([replace(self.record, observed_at=self.now + timedelta(seconds=1))],
                             symbol='DEMO', exchange_mic='XNAS',
                             on_date=date(2026, 9, 13), now=self.now)

    def test_invalid_identity_fields_are_rejected(self):
        for changes in ({'instrument_id': 'DEMO'}, {'issuer_id': 'ISS_BAD'},
                        {'symbol': None},
                        {'exchange_mic': 'NASDAQ'},
                        {'currency': 'PHP'}, {'source_uri': 'http://example.test/security'},
                        {'effective_to': date(2024, 1, 1)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.record, **changes)

    def test_stable_instrument_effective_date_is_verified(self):
        resolved = verify_instrument([self.record], instrument_id=self.record.instrument_id,
                                     on_date=date(2026, 9, 13), now=self.now)
        missing = verify_instrument([replace(self.record, effective_from=date(2027, 1, 1))],
                                    instrument_id=self.record.instrument_id,
                                    on_date=date(2026, 9, 13), now=self.now)
        self.assertEqual(resolved.status, 'resolved')
        self.assertEqual(missing.code, 'no_effective_instrument')


class DataRightsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 13, 7, tzinfo=timezone.utc)
        self.record = DataRightsRecord(
            provider_id='PRV_12345678', dataset_id='DATA_12345678', status='verified',
            permitted_uses=('internal_research',),
            terms_uri='https://example.test/terms/data', evidence_sha256='a' * 64,
            reviewed_at=self.now - timedelta(days=1),
            valid_until=self.now + timedelta(days=30))

    def decide(self, records, use_case='internal_research', at=None):
        return check_data_rights(records, provider_id='PRV_12345678',
                                 dataset_id='DATA_12345678', use_case=use_case,
                                 at=at or self.now)

    def test_explicit_use_is_allowed(self):
        self.assertEqual((self.decide([self.record]).allowed,
                          self.decide([self.record]).code),
                         (True, 'explicitly_permitted'))

    def test_unlicensed_use_and_pending_evidence_are_blocked(self):
        self.assertEqual(self.decide([self.record], 'redistribution').code,
                         'use_not_permitted')
        pending = replace(self.record, status='pending', permitted_uses=())
        self.assertEqual(self.decide([pending]).code, 'pending_evidence')

    def test_missing_expired_and_prohibited_evidence_are_distinct(self):
        self.assertEqual(self.decide([]).code, 'missing_evidence')
        expired = replace(self.record, valid_until=self.now)
        self.assertEqual(self.decide([expired]).code, 'expired_evidence')
        prohibited = replace(self.record, status='prohibited', permitted_uses=())
        self.assertEqual(self.decide([prohibited]).code, 'prohibited')

    def test_latest_review_controls_and_same_time_conflict_blocks(self):
        pending = replace(self.record, status='pending', permitted_uses=(),
                          evidence_sha256='b' * 64, reviewed_at=self.now)
        self.assertEqual(self.decide([self.record, pending]).code, 'pending_evidence')
        conflicting = replace(pending, status='prohibited', evidence_sha256='c' * 64)
        self.assertEqual(self.decide([pending, conflicting]).code, 'ambiguous_evidence')

    def test_invalid_rights_records_are_rejected(self):
        for changes in ({'status': 'assumed'}, {'provider_id': None},
                        {'permitted_uses': ('unknown',)},
                        {'evidence_sha256': 'short'}, {'terms_uri': 'file:///terms'},
                        {'valid_until': self.record.reviewed_at}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.record, **changes)
