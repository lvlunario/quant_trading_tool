from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from atlas.integrated_readiness import compose_integrated_prototype_readiness
from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.m5_release_candidate import M5ReleaseCandidatePlan
from atlas.m5_workflow_rehearsal import execute_m5_workflow_rehearsal
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.receipts import ImportReceipt
from atlas.weekly_report_readiness import assess_weekly_report_readiness
from atlas.weekly_research_report import build_synthetic_weekly_research_report


class M5WorkflowRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 19, 11, 0, tzinfo=timezone.utc)
        self.plan = M5ReleaseCandidatePlan(
            planned_at=datetime(2026, 11, 18, 11, 0,
                                tzinfo=timezone.utc),
            m4_review_sha256="a" * 64,
        )
        names = (
            "identity", "source_discovery", "rights_review",
            "capture_authorization", "extraction", "metric_release",
        )
        counts = (8, 8, 0, 0, 0, 0)
        blockers = (
            "identity_unresolved", "source_candidate_missing",
            "rights_review_incomplete", "capture_authorization_incomplete",
            "no_authorized_source_bytes", "no_verified_metric_evidence",
        )
        trace = M2AcceptanceTrace(
            self.now, 9,
            tuple(M2GateStage(name, count, 9 - count, blocker)
                  for name, count, blocker in zip(names, counts, blockers)),
        )
        weekly = build_synthetic_weekly_research_report(
            period_end=self.now.date(), generated_at=self.now)
        research = assess_weekly_report_readiness(weekly, trace)
        portfolio = ImportReceipt(
            1, "synthetic", "reconciled", "not_checked", 2, 0, 2,
            "replay_check_required",
        )
        self.integrated = compose_integrated_prototype_readiness(
            portfolio, research,
            build_synthetic_options_acceptance_evidence(),
            assessed_at=self.now,
        )
        self.rehearsal = execute_m5_workflow_rehearsal(
            self.plan, self.integrated, executed_at=self.now)

    def test_executes_all_four_reduced_workstreams_in_order(self):
        summary = self.rehearsal.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["workflow"]["workstreams_executed"],
             summary["workflow"]["workstreams_required"]),
            ("pre_freeze_workflow_rehearsal", "blocked", 4, 4),
        )
        self.assertEqual(
            [item["workstream"] for item in summary["workflow"]["steps"]],
            [
                "synthetic_portfolio_import_reconciliation",
                "read_only_research_workbench",
                "paper_options_scenario_controls",
                "weekly_review_decision_journal",
            ],
        )
        self.assertEqual(
            [item["sequence"] for item in summary["workflow"]["steps"]],
            [1, 2, 3, 4],
        )

    def test_expected_blocked_evidence_remains_visible(self):
        steps = self.rehearsal.public_summary()["workflow"]["steps"]
        self.assertEqual(steps[0]["evidence"], {
            "input_rows": 2,
            "rejected_rows": 0,
            "publishable_rows": 2,
            "fidelity_validated": False,
        })
        self.assertEqual(
            steps[1]["evidence"]["stage_passed_counts"],
            [8, 8, 0, 0, 0, 0],
        )
        self.assertFalse(steps[2]["evidence"]["real_chain_validated"])
        self.assertFalse(steps[3]["evidence"]["investment_conclusion"])

    def test_automated_pass_does_not_claim_zero_defects(self):
        summary = self.rehearsal.public_summary()
        self.assertEqual(
            summary["workflow"]["automated_execution_failures"], 0)
        self.assertEqual(summary["defect_register"], {
            "opened": True,
            "recorded_defect_count": 0,
            "critical_defect_status": "unknown_pending_formal_review",
            "independent_review_completed": False,
            "zero_defect_conclusion_supported": False,
        })

    def test_candidate_gate_remains_blocked_before_freeze(self):
        summary = self.rehearsal.public_summary()
        self.assertEqual(summary["timeline"], {
            "freeze_date": "2026-11-28",
            "days_to_freeze": 9,
            "candidate_build_frozen": False,
        })
        self.assertEqual(summary["candidate_gate"], {
            "ready": False,
            "blocker": "candidate_build_not_frozen",
            "rehearsal_only": True,
        })

    def test_wrong_types_times_and_authority_mutations_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, "invalid_m5_workflow_rehearsal_input"):
            execute_m5_workflow_rehearsal(
                {}, self.integrated, executed_at=self.now)
        with self.assertRaisesRegex(
                ValueError, "invalid_m5_workflow_rehearsal_input"):
            execute_m5_workflow_rehearsal(
                self.plan, self.integrated,
                executed_at=datetime(2026, 11, 19, 12, 0,
                                     tzinfo=timezone.utc),
            )
        for change in (
                {"automated_execution_failures": 1},
                {"critical_defect_status": "none"},
                {"candidate_build_frozen": True},
                {"candidate_gate_ready": True},
                {"independent_review_completed": True},
                {"founder_response_recorded": True},
                {"milestone_accepted": True},
                {"release_authorized": True},
                {"real_money_authorized": True}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m5_workflow_rehearsal"):
                replace(self.rehearsal, **change)

    def test_hash_redaction_and_authority_stay_fail_closed(self):
        duplicate = execute_m5_workflow_rehearsal(
            self.plan, self.integrated, executed_at=self.now)
        self.assertEqual(
            self.rehearsal.rehearsal_sha256,
            duplicate.rehearsal_sha256,
        )
        self.assertEqual(len(self.rehearsal.rehearsal_sha256), 64)
        summary = self.rehearsal.public_summary()
        for key in (
                "founder_response_recorded",
                "milestone_acceptance_recorded",
                "deployment_authorized",
                "private_data_authorized",
                "release_authorized",
                "real_money_authorized",
                "investment_performance_established"):
            self.assertFalse(summary[key])
        payload = json.dumps(summary).lower()
        for forbidden in (
                "plan_sha256", "integrated_readiness_sha256",
                "rehearsal_sha256", "account_id", "credential", "token",
                "secret", "source_uri", "holding", "symbol", "strike",
                "reserved_cash", "gross_cumulative_return"):
            self.assertNotIn(forbidden, payload)


class M5DefectRegisterDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).parents[1] / "docs" /
                    "M5_DEFECT_REGISTER.md").read_text()

    def test_register_is_open_but_not_completed(self):
        text = self.text.lower()
        for marker in (
                "opened_not_completed", "recorded defects: **0**",
                "unknown_pending_formal_review",
                "zero-defect conclusion: **not supported**"):
            self.assertIn(marker, text)

    def test_limitations_are_not_mislabeled_as_defects(self):
        text = self.text.lower()
        for marker in (
                "known limitations are not defect closures",
                "fidelity compatibility remains unverified",
                "private persistence and recovery remain unimplemented",
                "licensed sourced research remains blocked"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
