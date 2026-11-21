"""Pre-freeze rehearsal for the reduced local/synthetic M5 workflow."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .integrated_readiness import IntegratedPrototypeReadiness
from .m5_release_candidate import M5ReleaseCandidatePlan


FREEZE_DATE = date(2026, 11, 28)
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_WORKSTREAMS = (
    "synthetic_portfolio_import_reconciliation",
    "read_only_research_workbench",
    "paper_options_scenario_controls",
    "weekly_review_decision_journal",
)


def _summary_sha256(summary):
    payload = json.dumps(
        summary, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class M5WorkflowRehearsal:
    executed_at: datetime
    plan_sha256: str
    integrated_readiness_sha256: str
    schema_version: int = 1
    scope: str = "pre_freeze_reduced_candidate_rehearsal"
    workstreams_executed: int = len(_WORKSTREAMS)
    workstreams_required: int = len(_WORKSTREAMS)
    automated_execution_failures: int = 0
    defect_register_opened: bool = True
    recorded_defect_count: int = 0
    critical_defect_status: str = "unknown_pending_formal_review"
    candidate_build_frozen: bool = False
    candidate_gate_ready: bool = False
    independent_review_completed: bool = False
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
                local_date < date(2026, 11, 18) or
                _HEX_64.fullmatch(self.plan_sha256 or "") is None or
                _HEX_64.fullmatch(
                    self.integrated_readiness_sha256 or "") is None or
                self.scope != "pre_freeze_reduced_candidate_rehearsal" or
                self.workstreams_executed != len(_WORKSTREAMS) or
                self.workstreams_required != len(_WORKSTREAMS) or
                self.automated_execution_failures != 0 or
                self.defect_register_opened is not True or
                self.recorded_defect_count != 0 or
                self.critical_defect_status !=
                "unknown_pending_formal_review" or
                any(value is not False for value in (
                    self.candidate_build_frozen,
                    self.candidate_gate_ready,
                    self.independent_review_completed,
                    self.founder_response_recorded,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m5_workflow_rehearsal")

    def public_summary(self):
        local_date = self.executed_at.astimezone(
            ZoneInfo("Asia/Manila")).date()
        return {
            "schema_version": self.schema_version,
            "receipt_state": "pre_freeze_workflow_rehearsal",
            "status": "blocked",
            "phase": "M5 Release candidate preparation",
            "scope": self.scope,
            "executed_at": self.executed_at.isoformat(),
            "timeline": {
                "freeze_date": FREEZE_DATE.isoformat(),
                "days_to_freeze": (FREEZE_DATE - local_date).days,
                "candidate_build_frozen": False,
            },
            "workflow": {
                "execution_status":
                    "completed_with_expected_external_blocks",
                "workstreams_executed": self.workstreams_executed,
                "workstreams_required": self.workstreams_required,
                "automated_execution_failures":
                    self.automated_execution_failures,
                "steps": [
                    {
                        "sequence": 1,
                        "workstream": _WORKSTREAMS[0],
                        "status": "passed_synthetic_fixture_only",
                        "evidence": {
                            "input_rows": 2,
                            "rejected_rows": 0,
                            "publishable_rows": 2,
                            "fidelity_validated": False,
                        },
                    },
                    {
                        "sequence": 2,
                        "workstream": _WORKSTREAMS[1],
                        "status": "passed_with_expected_source_blocks",
                        "evidence": {
                            "universe_count": 9,
                            "stage_passed_counts": [8, 8, 0, 0, 0, 0],
                            "sourced_statement_count": 0,
                            "sourced_metric_count": 0,
                        },
                    },
                    {
                        "sequence": 3,
                        "workstream": _WORKSTREAMS[2],
                        "status": "passed_synthetic_controls_only",
                        "evidence": {
                            "scenario_count": 2,
                            "control_count": 4,
                            "real_chain_validated": False,
                            "actionable_ranking_authorized": False,
                        },
                    },
                    {
                        "sequence": 4,
                        "workstream": _WORKSTREAMS[3],
                        "status": "passed_synthetic_structure_only",
                        "evidence": {
                            "section_count": 4,
                            "investment_conclusion": False,
                            "publication_authorized": False,
                        },
                    },
                ],
            },
            "defect_register": {
                "opened": True,
                "recorded_defect_count": self.recorded_defect_count,
                "critical_defect_status": self.critical_defect_status,
                "independent_review_completed": False,
                "zero_defect_conclusion_supported": False,
            },
            "candidate_gate": {
                "ready": False,
                "blocker": "candidate_build_not_frozen",
                "rehearsal_only": True,
            },
            "founder_response_recorded": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
            "investment_performance_established": False,
        }

    @property
    def rehearsal_sha256(self):
        return _summary_sha256(self.public_summary())


def execute_m5_workflow_rehearsal(plan, integrated, *, executed_at):
    """Execute the four public-safe slices without promoting the M5 gate."""
    if (not isinstance(plan, M5ReleaseCandidatePlan) or
            not isinstance(integrated, IntegratedPrototypeReadiness) or
            not isinstance(executed_at, datetime) or
            executed_at.tzinfo is None or
            executed_at < plan.planned_at or
            integrated.assessed_at != executed_at):
        raise ValueError("invalid_m5_workflow_rehearsal_input")

    plan_summary = plan.public_summary()
    integrated_summary = integrated.public_summary()
    if (plan_summary.get("status") != "blocked" or
            plan_summary.get("scope") !=
            "reduced_local_synthetic_release_candidate" or
            plan_summary.get("candidate_scope_count") != 4 or
            plan_summary.get("deferred_scope_count") != 8 or
            plan_summary.get("acceptance_gates_ready") != 0 or
            plan_summary.get("acceptance_gates_required") != 5 or
            plan_summary.get("freeze_activated") is not False or
            integrated_summary.get("status") !=
            "synthetic_demo_ready_external_dependencies_blocked" or
            integrated_summary.get("portfolio") != {
                "status": "synthetic_reconciliation_complete",
                "input_rows": 2,
                "rejected_rows": 0,
                "publishable_rows": 2,
                "durable_replay_protection": False,
                "fidelity_validated": False,
            } or
            integrated_summary.get("research") != {
                "status": "blocked_sourced_report",
                "synthetic_section_count": 4,
                "universe_count": 9,
                "stage_passed_counts": [8, 8, 0, 0, 0, 0],
                "sourced_statement_count": 0,
                "sourced_metric_count": 0,
                "publication_authorized": False,
            } or
            integrated_summary.get("options") != {
                "status": "ready_for_founder_scenario_review",
                "scenario_count": 2,
                "control_count": 4,
                "real_chain_validated": False,
                "actionable_ranking_authorized": False,
            } or
            integrated_summary.get("capabilities") != {
                "read_only": True,
                "localhost_only": True,
                "authentication_implemented": False,
                "private_persistence_implemented": False,
                "network_retrieval_enabled": False,
                "order_path_enabled": False,
            } or
            integrated_summary.get("founder_acceptance_recorded") is not
            False or
            integrated_summary.get("milestone_acceptance_recorded") is not
            False or
            integrated_summary.get("release_authorized") is not False or
            integrated_summary.get("investment_performance_established") is
            not False):
        raise ValueError("invalid_m5_workflow_rehearsal_input")

    return M5WorkflowRehearsal(
        executed_at=executed_at,
        plan_sha256=plan.plan_sha256,
        integrated_readiness_sha256=_summary_sha256(integrated_summary),
    )
