"""Public-safe synthetic field-presence receipt for weekly claims."""
from dataclasses import dataclass
from datetime import datetime, timezone

from .weekly_source_manifest import (
    WeeklySourceCompletenessManifest,
    build_weekly_source_completeness_manifest,
)


@dataclass(frozen=True)
class SyntheticClaimBinding:
    """Declare schema fields present without accepting evidence values."""

    section: str
    provided_fields: tuple[str, ...]

    def validate_against(self, manifest: WeeklySourceCompletenessManifest):
        rule = next(
            (item for item in manifest.rules if item.section == self.section),
            None,
        )
        canonical = () if rule is None else tuple(
            field for field in rule.required_fields
            if field in self.provided_fields
        )
        if (rule is None or
                len(set(self.provided_fields)) != len(self.provided_fields) or
                canonical != self.provided_fields):
            raise ValueError('invalid_synthetic_claim_binding')


@dataclass(frozen=True)
class WeeklyClaimEvidenceReceipt:
    assessed_at: datetime
    manifest: WeeklySourceCompletenessManifest
    bindings: tuple[SyntheticClaimBinding, ...]

    def __post_init__(self):
        sections = tuple(rule.section for rule in self.manifest.rules)
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.manifest.as_of != self.assessed_at or
                any(not isinstance(binding, SyntheticClaimBinding)
                    for binding in self.bindings) or
                tuple(binding.section for binding in self.bindings) != sections):
            raise ValueError('invalid_weekly_claim_receipt')
        for binding in self.bindings:
            binding.validate_against(self.manifest)

    def public_summary(self):
        counts = []
        for rule, binding in zip(self.manifest.rules, self.bindings):
            required = len(rule.required_fields)
            provided = len(binding.provided_fields)
            counts.append({
                'section': rule.section,
                'required_field_count': required,
                'provided_field_count': provided,
                'missing_field_count': required - provided,
                'status': ('synthetic_fields_complete'
                           if required == provided
                           else 'blocked_missing_bindings'),
            })
        required_total = sum(item['required_field_count'] for item in counts)
        provided_total = sum(item['provided_field_count'] for item in counts)
        complete_total = sum(
            item['status'] == 'synthetic_fields_complete' for item in counts)
        return {
            'schema_version': 1,
            'mode': 'synthetic_field_presence_only',
            'status': 'blocked',
            'assessed_at': self.assessed_at.isoformat(),
            'rule_count': len(counts),
            'required_field_count': required_total,
            'provided_field_count': provided_total,
            'missing_field_count': required_total - provided_total,
            'synthetic_field_complete_count': complete_total,
            'blocked_claim_count': len(counts) - complete_total,
            'sections': counts,
            'evidence_values_status': 'not_accepted',
            'sourced_statement_count': 0,
            'sourced_metric_count': 0,
            'actual_report_eligible': False,
            'investment_conclusion': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'primary_blocker': 'claim_bindings_incomplete',
            'readiness': ('synthetic field-presence accounting only; evidence '
                          'values are not accepted or validated'),
        }


def build_synthetic_weekly_claim_evidence_receipt(*, assessed_at=None):
    """Build one fixed partial receipt; this API accepts no evidence values."""
    assessed_at = assessed_at or datetime.now(timezone.utc)
    manifest = build_weekly_source_completeness_manifest(as_of=assessed_at)
    fields = {rule.section: rule.required_fields for rule in manifest.rules}
    bindings = (
        SyntheticClaimBinding('observation', fields['observation']),
        SyntheticClaimBinding('hypothesis', fields['hypothesis'][:3]),
        SyntheticClaimBinding('counterargument', fields['counterargument'][:2]),
        SyntheticClaimBinding('missing_evidence', ()),
    )
    return WeeklyClaimEvidenceReceipt(assessed_at, manifest, bindings)
