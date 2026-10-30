from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import unittest

from atlas.reference import DataRightsRecord
from atlas.source_intake import (MAX_SOURCE_BYTES, SourceIntakeRequest,
                                 intake_research_source)


class SourceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        self.request = SourceIntakeRequest(
            'DOC_123456789ABC', 'INS_123456789ABC', 'PRV_12345678',
            'DATA_12345678', 'regulator_filing', 'application/pdf',
            self.now - timedelta(days=2), self.now - timedelta(days=1),
            'https://example.test/source.pdf')
        self.rights = DataRightsRecord(
            self.request.provider_id, self.request.dataset_id, 'verified',
            ('internal_research',), 'https://example.test/terms', 'a' * 64,
            self.now - timedelta(days=30), self.now + timedelta(days=30))

    def intake(self, content=b'%PDF-1.7\nsynthetic', request=None, rights=None):
        return intake_research_source(
            content, request or self.request,
            [self.rights] if rights is None else rights,
            use_case='internal_research', now=self.now)

    def test_permitted_exact_bytes_create_source_record(self):
        content = b'%PDF-1.7\nsynthetic'
        result = self.intake(content)
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.record.source_sha256, sha256(content).hexdigest())
        self.assertEqual(result.record.retrieved_at, self.now)
        self.assertEqual(result.byte_count, len(content))

    def test_exact_byte_change_changes_digest(self):
        first = self.intake(b'%PDF-1.7\na').record.source_sha256
        second = self.intake(b'%PDF-1.7\na\n').record.source_sha256
        self.assertNotEqual(first, second)

    def test_rights_fail_closed_before_record_creation(self):
        self.assertEqual(
            self.intake(b'not a pdf', rights=[]).codes,
            ('rights_missing_evidence',))
        cases = (
            ([], 'rights_missing_evidence'),
            ([replace(self.rights, status='pending', permitted_uses=())],
             'rights_pending_evidence'),
            ([replace(self.rights, permitted_uses=('customer_display',))],
             'rights_use_not_permitted'),
            ([replace(self.rights, valid_until=self.now)],
             'rights_expired_evidence'),
        )
        for rights, code in cases:
            with self.subTest(code=code):
                result = self.intake(rights=rights)
                self.assertEqual(result.codes, (code,))
                self.assertIsNone(result.record)

    def test_empty_oversize_and_wrong_input_type_are_rejected(self):
        self.assertEqual(self.intake(b'').codes, ('source_empty',))
        self.assertEqual(
            self.intake(b'x' * (MAX_SOURCE_BYTES + 1)).codes,
            ('source_too_large',))
        with self.assertRaisesRegex(ValueError, 'invalid_source_intake_request'):
            self.intake(bytearray(b'%PDF-1.7'))

    def test_text_encoding_and_pdf_signature_are_checked(self):
        text_request = replace(self.request, content_type='text/html')
        self.assertEqual(
            self.intake(b'\xff', request=text_request).codes,
            ('source_encoding_invalid',))
        self.assertEqual(
            self.intake(b'not a pdf').codes,
            ('source_content_signature_mismatch',))

    def test_invalid_metadata_and_future_timing_return_safe_code(self):
        for request in (
                replace(self.request, document_id='bad'),
                replace(self.request, provider_id='bad'),
                replace(self.request, available_at=self.now + timedelta(seconds=1))):
            with self.subTest(request=request):
                result = self.intake(request=request)
                self.assertEqual(result.codes, ('source_contract_invalid',))
                self.assertIsNone(result.record)

    def test_result_retains_metadata_not_content(self):
        result = self.intake()
        self.assertFalse(hasattr(result, 'content'))
        self.assertFalse(hasattr(result.record, 'content'))


if __name__ == '__main__':
    unittest.main()
