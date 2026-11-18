"""Fail-closed M5 reduced release-candidate scope and stabilization plan."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .m4_iteration_review import M4IterationReview


FREEZE_DATE = date(2026, 11, 28)
PROTOTYPE_TARGET_DATE = date(2026, 12, 12)
_HEX_64 = re.compile(r"[0-9a-f]{64}")

_CANDIDATE_SCOPE = (
    ("synthetic_portfolio_import_reconciliation",
     "checked_in_invented_fixture_only"),
    ("read_only_research_workbench",
     "public_metadata_and_synthetic_reports_only"),
    ("paper_options_scenario_controls",
     "deterministic_hypothetical_scenarios_only"),
    ("weekly_review_decision_journal",
     "no_investment_conclusion_or_release"),
)

_DEFERRED_SCOPE = (
    "fidelity_compatibility",
    "managed_authentication",
    "authorized_private_persistence",
    "private_record_restore_and_deletion",
    "licensed_market_and_options_data",
    "completed_data_rights_reviews",
    "production_hosting",
    "real_money_order_path",
)

_ACCEPTANCE_GATES = (
    ("candidate_workflow_regression",
     "candidate_build_not_frozen"),
    ("critical_defect_review",
     "candidate_defect_register_not_executed"),
    ("paper_event_retry_restart_review",
     "candidate_event_history_not_executed"),
    ("export_deletion_incident_walkthrough",
     "private_persistence_and_recovery_unimplemented"),
    ("rights_security_runbook_review",
     "independent_review_and_operational_evidence_incomplete"),
)

_ALLOWED_POST_FREEZE_CHANGES = (
    "critical_defect_fix",
    "regression_evidence",
    "security_evidence",
    "acceptance_evidence",
    "documentation_correction",
)

_BLOCKED_POST_FREEZE_CHANGES = (
    "new_feature",
    "new_data_provider",
    "unapproved_private_data",
    "production_deployment",
    "real_money_order_path",
)


def _summary_sha256(summary):
    payload = json.dumps(
        summary, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class M5ReleaseCandidatePlan:
    planned_at: datetime
    m4_review_sha256: str
    freeze_date: date = FREEZE_DATE
    prototype_target_date: date = PROTOTYPE_TARGET_DATE
    schema_version: int = 1
    scope: str = "reduced_local_synthetic_release_candidate"
    candidate_scope_count: int = len(_CANDIDATE_SCOPE)
    deferred_scope_count: int = len(_DEFERRED_SCOPE)
    acceptance_gates_ready: int = 0
    acceptance_gates_required: int = len(_ACCEPTANCE_GATES)
    freeze_activated: bool = False
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    deployment_authorized: bool = False
    private_data_authorized: bool = False
    release_authorized: bool = False
    real_money_authorized: bool = False

    def __post_init__(self):
        local_date = (
            self.planned_at.astimezone(ZoneInfo("Asia/Manila")).date()
            if isinstance(self.planned_at, datetime) and
            self.planned_at.tzinfo is not None else None
        )
        if (self.schema_version != 1 or
                local_date is None or
                local_date < date(2026, 11, 16) or
                _HEX_64.fullmatch(self.m4_review_sha256 or "") is None or
                self.freeze_date != FREEZE_DATE or
                self.prototype_target_date != PROTOTYPE_TARGET_DATE or
                self.scope != "reduced_local_synthetic_release_candidate" or
                self.candidate_scope_count != len(_CANDIDATE_SCOPE) or
                self.deferred_scope_count != len(_DEFERRED_SCOPE) or
                self.acceptance_gates_ready != 0 or
                self.acceptance_gates_required != len(_ACCEPTANCE_GATES) or
                any(value is not False for value in (
                    self.freeze_activated,
                    self.founder_response_recorded,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m5_release_candidate_plan")

    def public_summary(self):
        local_date = self.planned_at.astimezone(
            ZoneInfo("Asia/Manila")).date()
        days_to_freeze = (self.freeze_date - local_date).days
        return {
            "schema_version": self.schema_version,
            "receipt_state": "scope_freeze_plan",
            "status": "blocked",
            "phase": "M5 Release candidate preparation",
            "scope": self.scope,
            "planned_at": self.planned_at.isoformat(),
            "timeline": {
                "freeze_date": self.freeze_date.isoformat(),
                "freeze_timing": (
                    "scheduled" if days_to_freeze > 0 else
                    "due" if days_to_freeze == 0 else
                    "elapsed_without_activation"
                ),
                "days_to_freeze": days_to_freeze,
                "prototype_target_date":
                    self.prototype_target_date.isoformat(),
                "days_to_prototype_target":
                    (self.prototype_target_date - local_date).days,
            },
            "candidate_scope": [
                {"workstream": workstream, "boundary": boundary}
                for workstream, boundary in _CANDIDATE_SCOPE
            ],
            "candidate_scope_count": self.candidate_scope_count,
            "deferred_scope": list(_DEFERRED_SCOPE),
            "deferred_scope_count": self.deferred_scope_count,
            "acceptance_gates": [
                {
                    "gate": gate,
                    "status": "blocked",
                    "blocker": blocker,
                    "ready": False,
                }
                for gate, blocker in _ACCEPTANCE_GATES
            ],
            "acceptance_gates_ready": self.acceptance_gates_ready,
            "acceptance_gates_required": self.acceptance_gates_required,
            "post_freeze_change_policy": {
                "active": False,
                "allowed": list(_ALLOWED_POST_FREEZE_CHANGES),
                "blocked": list(_BLOCKED_POST_FREEZE_CHANGES),
            },
            "recommendation": (
                "review_reduced_scope_for_freeze_on_2026_11_28"
            ),
            "freeze_activated": False,
            "founder_response_recorded": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
        }

    @property
    def plan_sha256(self):
        return _summary_sha256(self.public_summary())


def prepare_m5_release_candidate_plan(review, *, planned_at):
    """Bind the reduced M5 plan to the blocked M4 review evidence."""
    if (not isinstance(review, M4IterationReview) or
            not isinstance(planned_at, datetime) or
            planned_at.tzinfo is None or
            planned_at < review.reviewed_at):
        raise ValueError("invalid_m5_release_candidate_input")
    summary = review.public_summary()
    if (summary.get("receipt_state") != "review_packet" or
            summary.get("status") != "blocked" or
            summary.get("demo", {}).get("private_criteria_ready") != 0 or
            summary.get("demo", {}).get("private_criteria_required") != 5 or
            summary.get("recommendation_count") != 3 or
            "freeze_scope_for_stabilization_on_2026_11_28" not in {
                item.get("decision")
                for item in summary.get("recommendations", ())
            } or
            any(summary.get(key) is not False for key in (
                "meeting_completed",
                "founder_response_recorded",
                "decisions_approved",
                "milestone_acceptance_recorded",
                "deployment_authorized",
                "private_data_authorized",
                "release_authorized",
                "real_money_authorized"))):
        raise ValueError("invalid_m5_release_candidate_input")
    return M5ReleaseCandidatePlan(
        planned_at=planned_at,
        m4_review_sha256=review.review_sha256,
    )
