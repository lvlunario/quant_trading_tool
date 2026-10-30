"""Versioned field requirements for a source-complete weekly report."""
from dataclasses import dataclass
from datetime import datetime, timezone


_RULE_SPECS = (
    (
        'observation',
        'permitted_source_binding',
        ('claim_id', 'as_of', 'instrument_id', 'source_document_id',
         'observation_id', 'rights_decision', 'available_at',
         'extraction_quality'),
    ),
    (
        'hypothesis',
        'explicit_assumption_with_support',
        ('claim_id', 'as_of', 'supporting_claim_ids', 'assumption_label',
         'disconfirming_check'),
    ),
    (
        'counterargument',
        'explicit_challenge_with_support_or_gap',
        ('claim_id', 'as_of', 'challenged_claim_ids',
         'supporting_claim_ids_or_gap', 'disconfirming_check'),
    ),
    (
        'missing_evidence',
        'explicit_gap_with_next_check',
        ('claim_id', 'as_of', 'gap_code', 'blocked_claim_ids', 'next_check'),
    ),
)


@dataclass(frozen=True)
class WeeklySourceRule:
    section: str
    evidence_requirement: str
    required_fields: tuple[str, ...]
    allows_unbound_factual_claim: bool = False

    def __post_init__(self):
        expected = next((spec for spec in _RULE_SPECS
                         if spec[0] == self.section), None)
        if (expected is None or
                self.evidence_requirement != expected[1] or
                self.required_fields != expected[2] or
                self.allows_unbound_factual_claim is not False):
            raise ValueError('invalid_weekly_source_rule')

    def public_summary(self):
        return {
            'section': self.section,
            'evidence_requirement': self.evidence_requirement,
            'required_fields': list(self.required_fields),
            'required_field_count': len(self.required_fields),
            'allows_unbound_factual_claim': False,
        }


@dataclass(frozen=True)
class WeeklySourceCompletenessManifest:
    as_of: datetime
    rules: tuple[WeeklySourceRule, ...]

    def __post_init__(self):
        if (not isinstance(self.as_of, datetime) or
                self.as_of.tzinfo is None or
                tuple(rule.section for rule in self.rules) !=
                tuple(spec[0] for spec in _RULE_SPECS) or
                any(not isinstance(rule, WeeklySourceRule)
                    for rule in self.rules)):
            raise ValueError('invalid_weekly_source_manifest')

    def public_summary(self):
        return {
            'schema_version': 1,
            'status': 'blocked',
            'as_of': self.as_of.isoformat(),
            'rule_count': len(self.rules),
            'rules': [rule.public_summary() for rule in self.rules],
            'evidence_values_status': 'not_provided',
            'complete_claim_count': 0,
            'sourced_statement_count': 0,
            'sourced_metric_count': 0,
            'actual_report_eligible': False,
            'investment_conclusion': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'primary_blocker': 'source_evidence_not_provided',
            'readiness': ('field requirements are defined; no claim evidence '
                          'values have been provided'),
        }


def build_weekly_source_completeness_manifest(*, as_of=None):
    """Build the fixed field contract without supplying source evidence."""
    as_of = as_of or datetime.now(timezone.utc)
    rules = tuple(WeeklySourceRule(*spec) for spec in _RULE_SPECS)
    return WeeklySourceCompletenessManifest(as_of, rules)
