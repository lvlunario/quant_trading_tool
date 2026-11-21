"""Fail-closed November 14 M4 checkpoint candidate and execution record."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .integrated_readiness import IntegratedPrototypeReadiness
from .private_environment_readiness import (
    M4_DEPENDENCIES,
    PrivateEnvironmentReadiness,
)


M4_TARGET_DATE = date(2026, 11, 14)
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_RESEARCH_COUNTS = (8, 8, 0, 0, 0, 0)
_RECOMMENDATION = (
    "defer_private_milestone_continue_local_synthetic_fallback"
)


def _summary_sha256(summary):
    payload = json.dumps(
        summary, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class M4CheckpointCandidate:
    assessed_at: datetime
    integrated_readiness_sha256: str
    private_environment_sha256: str
    target_date: date = M4_TARGET_DATE
    schema_version: int = 1
    scope: str = "local_synthetic_checkpoint_candidate"
    portfolio_input_rows: int = 2
    research_stage_passed_counts: tuple[int, ...] = _RESEARCH_COUNTS
    option_scenario_count: int = 2
    option_control_count: int = 4
    private_criteria_ready: int = 0
    private_criteria_required: int = 5
    continue_local_synthetic_fallback: bool = True
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    deployment_authorized: bool = False
    private_data_authorized: bool = False
    release_authorized: bool = False
    real_money_authorized: bool = False

    def __post_init__(self):
        if (self.schema_version != 1 or
                not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.target_date != M4_TARGET_DATE or
                _HEX_64.fullmatch(
                    self.integrated_readiness_sha256 or "") is None or
                _HEX_64.fullmatch(
                    self.private_environment_sha256 or "") is None or
                self.scope != "local_synthetic_checkpoint_candidate" or
                self.portfolio_input_rows != 2 or
                self.research_stage_passed_counts != _RESEARCH_COUNTS or
                self.option_scenario_count != 2 or
                self.option_control_count != 4 or
                self.private_criteria_ready != 0 or
                self.private_criteria_required != len(M4_DEPENDENCIES) or
                self.continue_local_synthetic_fallback is not True or
                any(value is not False for value in (
                    self.founder_response_recorded,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m4_checkpoint_candidate")

    def public_summary(self):
        local_date = self.assessed_at.astimezone(
            ZoneInfo("Asia/Manila")).date()
        days_to_checkpoint = (self.target_date - local_date).days
        checkpoint_status = (
            "scheduled" if days_to_checkpoint > 0 else
            "due" if days_to_checkpoint == 0 else
            "elapsed"
        )
        return {
            "schema_version": self.schema_version,
            "receipt_state": "candidate",
            "status": "blocked",
            "phase": "M4 Private application",
            "scope": self.scope,
            "assessed_at": self.assessed_at.isoformat(),
            "checkpoint_date": self.target_date.isoformat(),
            "checkpoint_status": checkpoint_status,
            "days_to_checkpoint": days_to_checkpoint,
            "aggregate_evidence": {
                "local_synthetic_status":
                    "synthetic_demo_ready_external_dependencies_blocked",
                "portfolio_input_rows": self.portfolio_input_rows,
                "research_stage_passed_counts":
                    list(self.research_stage_passed_counts),
                "option_scenario_count": self.option_scenario_count,
                "option_control_count": self.option_control_count,
                "read_only": True,
                "localhost_only": True,
            },
            "private_environment": {
                "status": "private_environment_blocked_external_evidence",
                "criteria_ready": self.private_criteria_ready,
                "criteria_required": self.private_criteria_required,
                "criteria_deferred": self.private_criteria_required,
            },
            "criteria": [
                {
                    "criterion": item.name,
                    "status": item.status,
                    "blocker": item.blocker,
                    "recommendation": "recommend_defer",
                }
                for item in M4_DEPENDENCIES
            ],
            "overall_recommendation": _RECOMMENDATION,
            "continue_local_synthetic_fallback":
                self.continue_local_synthetic_fallback,
            "founder_response_recorded": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
        }

    @property
    def candidate_sha256(self):
        return _summary_sha256(self.public_summary())


@dataclass(frozen=True)
class M4CheckpointExecution:
    executed_at: datetime
    candidate_sha256: str
    target_date: date = M4_TARGET_DATE
    schema_version: int = 1
    scope: str = "local_synthetic_checkpoint_execution"
    private_criteria_ready: int = 0
    private_criteria_required: int = 5
    disposition: str = "deferred_pending_explicit_founder_disposition"
    continue_local_synthetic_fallback: bool = True
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    deployment_authorized: bool = False
    private_data_authorized: bool = False
    release_authorized: bool = False
    real_money_authorized: bool = False

    def __post_init__(self):
        local_date = (
            self.executed_at.astimezone(ZoneInfo("Asia/Manila")).date()
            if isinstance(self.executed_at, datetime) and
            self.executed_at.tzinfo is not None else None
        )
        if (self.schema_version != 1 or
                local_date is None or
                local_date < M4_TARGET_DATE or
                self.target_date != M4_TARGET_DATE or
                _HEX_64.fullmatch(self.candidate_sha256 or "") is None or
                self.scope != "local_synthetic_checkpoint_execution" or
                self.private_criteria_ready != 0 or
                self.private_criteria_required != len(M4_DEPENDENCIES) or
                self.disposition !=
                "deferred_pending_explicit_founder_disposition" or
                self.continue_local_synthetic_fallback is not True or
                any(value is not False for value in (
                    self.founder_response_recorded,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m4_checkpoint_execution")

    def public_summary(self):
        local_date = self.executed_at.astimezone(
            ZoneInfo("Asia/Manila")).date()
        days_after_checkpoint = (local_date - self.target_date).days
        return {
            "schema_version": self.schema_version,
            "receipt_state": "executed",
            "status": "blocked",
            "phase": "M4 Private application",
            "scope": self.scope,
            "executed_at": self.executed_at.isoformat(),
            "checkpoint_date": self.target_date.isoformat(),
            "checkpoint_status": (
                "executed_due" if days_after_checkpoint == 0 else
                "executed_late"
            ),
            "days_after_checkpoint": days_after_checkpoint,
            "candidate_bound": True,
            "private_environment": {
                "criteria_ready": self.private_criteria_ready,
                "criteria_required": self.private_criteria_required,
                "criteria_deferred": self.private_criteria_required,
            },
            "criteria": [
                {
                    "criterion": item.name,
                    "status": item.status,
                    "blocker": item.blocker,
                    "disposition": "deferred",
                }
                for item in M4_DEPENDENCIES
            ],
            "disposition": self.disposition,
            "overall_recommendation": _RECOMMENDATION,
            "continue_local_synthetic_fallback":
                self.continue_local_synthetic_fallback,
            "founder_response_recorded": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
        }

    @property
    def execution_sha256(self):
        return _summary_sha256(self.public_summary())


def assess_m4_checkpoint_candidate(integrated, private_environment):
    """Compose typed aggregate evidence into an explicit deferral candidate."""
    if (not isinstance(integrated, IntegratedPrototypeReadiness) or
            not isinstance(private_environment, PrivateEnvironmentReadiness) or
            integrated.assessed_at != private_environment.assessed_at):
        raise ValueError("invalid_m4_checkpoint_input")
    integrated_summary = integrated.public_summary()
    private_summary = private_environment.public_summary()
    expected_criteria = [
        {
            "name": item.name,
            "status": item.status,
            "blocker": item.blocker,
            "ready": False,
        }
        for item in M4_DEPENDENCIES
    ]
    if (integrated_summary.get("status") !=
            "synthetic_demo_ready_external_dependencies_blocked" or
            integrated_summary.get("portfolio") != {
                "status": "synthetic_reconciliation_complete",
                "input_rows": 2,
                "rejected_rows": 0,
                "publishable_rows": 2,
                "durable_replay_protection": False,
                "fidelity_validated": False,
            } or
            integrated_summary.get("research", {}).get(
                "stage_passed_counts") != list(_RESEARCH_COUNTS) or
            integrated_summary.get("options", {}).get(
                "scenario_count") != 2 or
            integrated_summary.get("options", {}).get("control_count") != 4 or
            integrated_summary.get("capabilities") != {
                "read_only": True,
                "localhost_only": True,
                "authentication_implemented": False,
                "private_persistence_implemented": False,
                "network_retrieval_enabled": False,
                "order_path_enabled": False,
            } or
            integrated_summary.get("milestone_acceptance_recorded") is not
            False or
            integrated_summary.get("release_authorized") is not False or
            private_summary.get("criteria") != expected_criteria or
            (private_summary.get("criteria_ready"),
             private_summary.get("criteria_total"),
             private_summary.get("criteria_blocked")) != (0, 5, 5) or
            private_summary.get("milestone_acceptance_recorded") is not
            False or
            private_summary.get("deployment_authorized") is not False or
            private_summary.get("private_data_authorized") is not False or
            private_summary.get("release_authorized") is not False or
            private_summary.get("real_money_authorized") is not False):
        raise ValueError("invalid_m4_checkpoint_input")
    return M4CheckpointCandidate(
        assessed_at=integrated.assessed_at,
        integrated_readiness_sha256=_summary_sha256(integrated_summary),
        private_environment_sha256=_summary_sha256(private_summary),
    )


def execute_m4_checkpoint(candidate, *, executed_at):
    """Record an elapsed/due checkpoint without manufacturing acceptance."""
    if (not isinstance(candidate, M4CheckpointCandidate) or
            not isinstance(executed_at, datetime) or
            executed_at.tzinfo is None or
            executed_at < candidate.assessed_at):
        raise ValueError("invalid_m4_checkpoint_execution_input")
    candidate_summary = candidate.public_summary()
    expected_criteria = [
        {
            "criterion": item.name,
            "status": item.status,
            "blocker": item.blocker,
            "recommendation": "recommend_defer",
        }
        for item in M4_DEPENDENCIES
    ]
    if (candidate_summary.get("receipt_state") != "candidate" or
            candidate_summary.get("status") != "blocked" or
            candidate_summary.get("criteria") != expected_criteria or
            candidate_summary.get("overall_recommendation") !=
            _RECOMMENDATION or
            candidate_summary.get("founder_response_recorded") is not False or
            candidate_summary.get("milestone_acceptance_recorded") is not
            False or
            candidate_summary.get("deployment_authorized") is not False or
            candidate_summary.get("private_data_authorized") is not False or
            candidate_summary.get("release_authorized") is not False or
            candidate_summary.get("real_money_authorized") is not False):
        raise ValueError("invalid_m4_checkpoint_execution_input")
    return M4CheckpointExecution(
        executed_at=executed_at,
        candidate_sha256=candidate.candidate_sha256,
    )
