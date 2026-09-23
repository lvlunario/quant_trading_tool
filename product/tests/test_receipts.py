import unittest
from atlas.receipts import import_receipt


class ReceiptTests(unittest.TestCase):
    def report(self, **changes):
        result = dict(mode='synthetic', status='reconciled', replay_status='recorded',
                      outcomes=[dict(row_number=1, status='accepted', code='ok')],
                      errors=[], publishable_row_count=1,
                      account_totals={'PRIVATE': '100'}, path='PRIVATE', symbol='PRIVATE')
        result.update(changes)
        return result

    def test_allowlist_excludes_private_fields(self):
        receipt = import_receipt(self.report()).to_dict()
        self.assertEqual(receipt, dict(schema_version=1, mode='synthetic',
                         reconciliation='reconciled', replay='recorded', input_rows=1,
                         rejected_rows=0, publishable_rows=1, decision='eligible'))
        self.assertNotIn('PRIVATE', str(receipt))

    def test_replay_and_unchecked_are_not_eligible(self):
        self.assertEqual(import_receipt(self.report(replay_status='not_checked')).decision,
                         'replay_check_required')
        self.assertEqual(import_receipt(self.report(replay_status='exact_replay',
                         publishable_row_count=0)).decision, 'duplicate')

    def test_blocked_takes_precedence_over_replay(self):
        receipt = import_receipt(self.report(status='blocked', errors=['mismatch'],
                                 replay_status='exact_replay', publishable_row_count=0))
        self.assertEqual(receipt.decision, 'blocked')

    def test_inconsistent_or_missing_evidence_rejected(self):
        for changes in (dict(publishable_row_count=True), dict(publishable_row_count=2),
                        dict(replay_status='unknown'), dict(outcomes=[]),
                        dict(errors=['mismatch']), dict(status='blocked'),
                        dict(replay_status='exact_replay'),
                        dict(outcomes=[dict(row_number=2, status='accepted')]),
                        dict(outcomes=[dict(row_number=1, status='rejected')])):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                import_receipt(self.report(**changes))
