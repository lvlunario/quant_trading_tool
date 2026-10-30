from dataclasses import replace
from datetime import datetime, timezone
import unittest

from atlas.weekly_source_manifest import (
    WeeklySourceCompletenessManifest, WeeklySourceRule,
    build_weekly_source_completeness_manifest,
)


class WeeklySourceManifestTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 10, 9, 11, 0, tzinfo=timezone.utc)
        self.manifest = build_weekly_source_completeness_manifest(
            as_of=self.as_of)

    def test_rules_follow_weekly_section_order_and_evidence_semantics(self):
        self.assertEqual(
            [(rule.section, rule.evidence_requirement)
             for rule in self.manifest.rules],
            [('observation', 'permitted_source_binding'),
             ('hypothesis', 'explicit_assumption_with_support'),
             ('counterargument',
              'explicit_challenge_with_support_or_gap'),
             ('missing_evidence', 'explicit_gap_with_next_check')])

    def test_observations_require_exact_permitted_evidence_binding(self):
        observation = self.manifest.rules[0]
        self.assertEqual(
            observation.required_fields,
            ('claim_id', 'as_of', 'instrument_id', 'source_document_id',
             'observation_id', 'rights_decision', 'available_at',
             'extraction_quality'))
        self.assertFalse(observation.allows_unbound_factual_claim)

    def test_inference_rules_require_labels_support_and_challenges(self):
        hypothesis, counterargument, gap = self.manifest.rules[1:]
        self.assertIn('assumption_label', hypothesis.required_fields)
        self.assertIn('supporting_claim_ids', hypothesis.required_fields)
        self.assertIn('challenged_claim_ids', counterargument.required_fields)
        self.assertIn('supporting_claim_ids_or_gap',
                      counterargument.required_fields)
        self.assertIn('next_check', gap.required_fields)
        self.assertTrue(all(
            rule.required_fields[:2] == ('claim_id', 'as_of')
            for rule in self.manifest.rules))

    def test_changed_rule_or_unbound_fact_permission_fails_closed(self):
        rule = self.manifest.rules[0]
        for change in (
                {'evidence_requirement': 'citation_optional'},
                {'required_fields': rule.required_fields[:-1]},
                {'allows_unbound_factual_claim': True}):
            with self.assertRaisesRegex(ValueError,
                                        'invalid_weekly_source_rule'):
                replace(rule, **change)

    def test_manifest_rejects_missing_reordered_or_naive_contracts(self):
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_source_manifest'):
            WeeklySourceCompletenessManifest(
                self.as_of, self.manifest.rules[:-1])
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_source_manifest'):
            WeeklySourceCompletenessManifest(
                self.as_of, tuple(reversed(self.manifest.rules)))
        with self.assertRaisesRegex(ValueError,
                                    'invalid_weekly_source_manifest'):
            WeeklySourceCompletenessManifest(
                datetime(2026, 10, 9, 11, 0), self.manifest.rules)


if __name__ == '__main__':
    unittest.main()
