"""Public-safe asynchronous M4 concept and iteration review packet."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .m4_checkpoint import M4CheckpointExecution


REVIEW_DATE = date(2026, 11, 16)
STABILIZATION_DATE = date(2026, 11, 28)
PROTOTYPE_TARGET_DATE = date(2026, 12, 12)
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_DEPENDENCIES = (
    "representative_authorized_fidelity_export",
    "private_environment_owner_review",
    "completed_data_rights_and_licensed_dataset_evidence",
    "founder_m3_and_m4_disposition",
    "dated_public_evidence_catch_up",
)
_RECOMMENDATIONS = (
    "adopt_reduced_local_synthetic_release_candidate",
    "defer_authenticated_private_milestone_until_controls_exist",
    "freeze_scope_for_stabilization_on_2026_11_28",
)


def _summary_sha256(summary):
    payload = json.dumps(
        summary, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class M4IterationReview:
    reviewed_at: datetime
    execution_sha256: str
    review_date: date = REVIEW_DATE
    stabilization_date: date = STABILIZATION_DATE
    prototype_target_date: date = PROTOTYPE_TARGET_DATE
    schema_version: int = 1
    scope: str = "m4_asynchronous_iteration_review"
    private_criteria_ready: int = 0
    private_criteria_required: int = 5
    recommendation_count: int = 3
    meeting_completed: bool = False
    founder_response_recorded: bool = False
    decisions_approved: bool = False
    milestone_accepted: bool = False
    deployment_authorized: bool = False
    private_data_authorized: bool = False
    release_authorized: bool = False
    real_money_authorized: bool = False

    def __post_init__(self):
        local_date = (
            self.reviewed_at.astimezone(ZoneInfo("Asia/Manila")).date()
            if isinstance(self.reviewed_at, datetime) and
            self.reviewed_at.tzinfo is not None else None
        )
        if (self.schema_version != 1 or
                local_date is None or
                local_date < REVIEW_DATE or
                _HEX_64.fullmatch(self.execution_sha256 or "") is None or
                self.review_date != REVIEW_DATE or
                self.stabilization_date != STABILIZATION_DATE or
                self.prototype_target_date != PROTOTYPE_TARGET_DATE or
                self.scope != "m4_asynchronous_iteration_review" or
                self.private_criteria_ready != 0 or
                self.private_criteria_required != 5 or
                self.recommendation_count != len(_RECOMMENDATIONS) or
                any(value is not False for value in (
                    self.meeting_completed,
                    self.founder_response_recorded,
                    self.decisions_approved,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m4_iteration_review")

    def public_summary(self):
        local_date = self.reviewed_at.astimezone(
            ZoneInfo("Asia/Manila")).date()
        return {
            "schema_version": self.schema_version,
            "receipt_state": "review_packet",
            "status": "blocked",
            "phase": "M4 Private application",
            "scope": self.scope,
            "reviewed_at": self.reviewed_at.isoformat(),
            "scheduled_review_date": self.review_date.isoformat(),
            "review_timing": (
                "prepared_on_date" if local_date == self.review_date else
                "prepared_late"
            ),
            "timeline": {
                "stabilization_date": self.stabilization_date.isoformat(),
                "days_to_stabilization":
                    (self.stabilization_date - local_date).days,
                "prototype_target_date":
                    self.prototype_target_date.isoformat(),
                "days_to_prototype_target":
                    (self.prototype_target_date - local_date).days,
            },
            "demo": {
                "checkpoint_receipt_state": "executed",
                "checkpoint_status": "blocked",
                "checkpoint_bound": True,
                "private_criteria_ready": self.private_criteria_ready,
                "private_criteria_required": self.private_criteria_required,
                "private_criteria_deferred": self.private_criteria_required,
                "continue_local_synthetic_fallback": True,
            },
            "planned_vs_shipped": [
                {
                    "planned": "authenticated_private_read_only_prototype",
                    "shipped": "localhost_synthetic_read_only_checkpoint",
                    "state": "reduced_scope_only",
                },
                {
                    "planned": "five_private_environment_controls",
                    "shipped": "zero_of_five_controls_evidenced",
                    "state": "blocked",
                },
                {
                    "planned": "dated_weekly_public_evidence_update",
                    "shipped": "november_14_update_not_present",
                    "state": "catch_up_required_without_backdating",
                },
            ],
            "dependencies": list(_DEPENDENCIES),
            "recommendations": [
                {"decision": item, "status": "recommend"}
                for item in _RECOMMENDATIONS
            ],
            "recommendation_count": self.recommendation_count,
            "meeting_completed": False,
            "founder_response_recorded": False,
            "decisions_approved": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
        }

    @property
    def review_sha256(self):
        return _summary_sha256(self.public_summary())


def prepare_m4_iteration_review(execution, *, reviewed_at):
    """Prepare a three-decision review packet without recording approval."""
    if (not isinstance(execution, M4CheckpointExecution) or
            not isinstance(reviewed_at, datetime) or
            reviewed_at.tzinfo is None or
            reviewed_at < execution.executed_at):
        raise ValueError("invalid_m4_iteration_review_input")
    summary = execution.public_summary()
    if (summary.get("receipt_state") != "executed" or
            summary.get("status") != "blocked" or
            summary.get("candidate_bound") is not True or
            summary.get("private_environment") != {
                "criteria_ready": 0,
                "criteria_required": 5,
                "criteria_deferred": 5,
            } or
            len(summary.get("criteria", ())) != 5 or
            any(item.get("disposition") != "deferred"
                for item in summary.get("criteria", ())) or
            summary.get("continue_local_synthetic_fallback") is not True or
            summary.get("founder_response_recorded") is not False or
            summary.get("milestone_acceptance_recorded") is not False or
            summary.get("deployment_authorized") is not False or
            summary.get("private_data_authorized") is not False or
            summary.get("release_authorized") is not False or
            summary.get("real_money_authorized") is not False):
        raise ValueError("invalid_m4_iteration_review_input")
    return M4IterationReview(
        reviewed_at=reviewed_at,
        execution_sha256=execution.execution_sha256,
    )
