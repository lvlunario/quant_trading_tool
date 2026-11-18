from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from atlas.m4_checkpoint import M4CheckpointExecution
from atlas.m4_iteration_review import prepare_m4_iteration_review
from atlas.m5_release_candidate import prepare_m5_release_candidate_plan


class M5ReleaseCandidatePlanTests(unittest.TestCase):
    def setUp(self):
        self.executed_at = datetime(
            2026, 11, 15, 12, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(
            2026, 11, 16, 11, 30, tzinfo=timezone.utc)
        execution = M4CheckpointExecution(
            executed_at=self.executed_at,
            candidate_sha256="a" * 64,
        )
        self.review = prepare_m4_iteration_review(
            execution, reviewed_at=self.reviewed_at)
        self.planned_at = datetime(
            2026, 11, 18, 11, 0, tzinfo=timezone.utc)
        self.plan = prepare_m5_release_candidate_plan(
            self.review, planned_at=self.planned_at)

    def test_reduced_candidate_scope_and_deferrals_are_exact(self):
        summary = self.plan.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["candidate_scope_count"],
             summary["deferred_scope_count"]),
            ("scope_freeze_plan", "blocked", 4, 8),
        )
        self.assertEqual(
            [item["workstream"] for item in summary["candidate_scope"]],
            [
                "synthetic_portfolio_import_reconciliation",
                "read_only_research_workbench",
                "paper_options_scenario_controls",
                "weekly_review_decision_journal",
            ],
        )
        self.assertIn("fidelity_compatibility", summary["deferred_scope"])
        self.assertIn("real_money_order_path", summary["deferred_scope"])

    def test_all_five_acceptance_gates_remain_blocked(self):
        summary = self.plan.public_summary()
        self.assertEqual(
            (summary["acceptance_gates_ready"],
             summary["acceptance_gates_required"]),
            (0, 5),
        )
        self.assertEqual(len(summary["acceptance_gates"]), 5)
        self.assertTrue(all(
            item["status"] == "blocked" and item["ready"] is False
            for item in summary["acceptance_gates"]))
        self.assertIn(
            "private_persistence_and_recovery_unimplemented",
            [item["blocker"] for item in summary["acceptance_gates"]],
        )

    def test_post_freeze_policy_limits_changes_to_stabilization(self):
        policy = self.plan.public_summary()["post_freeze_change_policy"]
        self.assertFalse(policy["active"])
        self.assertEqual(
            policy["allowed"],
            [
                "critical_defect_fix",
                "regression_evidence",
                "security_evidence",
                "acceptance_evidence",
                "documentation_correction",
            ],
        )
        self.assertIn("new_feature", policy["blocked"])
        self.assertIn("production_deployment", policy["blocked"])
        self.assertIn("real_money_order_path", policy["blocked"])

    def test_timeline_is_manila_dated_and_does_not_auto_activate(self):
        summary = self.plan.public_summary()
        self.assertEqual(
            summary["timeline"],
            {
                "freeze_date": "2026-11-28",
                "freeze_timing": "scheduled",
                "days_to_freeze": 10,
                "prototype_target_date": "2026-12-12",
                "days_to_prototype_target": 24,
            },
        )
        self.assertFalse(summary["freeze_activated"])
        self.assertEqual(
            summary["recommendation"],
            "review_reduced_scope_for_freeze_on_2026_11_28",
        )

    def test_wrong_review_time_and_authority_mutations_fail_closed(self):
        with self.assertRaisesRegex(
                ValueError, "invalid_m5_release_candidate_input"):
            prepare_m5_release_candidate_plan(
                {}, planned_at=self.planned_at)
        with self.assertRaisesRegex(
                ValueError, "invalid_m5_release_candidate_input"):
            prepare_m5_release_candidate_plan(
                self.review,
                planned_at=self.reviewed_at - timedelta(seconds=1),
            )
        for change in (
                {"freeze_activated": True},
                {"founder_response_recorded": True},
                {"milestone_accepted": True},
                {"deployment_authorized": True},
                {"private_data_authorized": True},
                {"release_authorized": True},
                {"real_money_authorized": True},
                {"acceptance_gates_ready": 1}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m5_release_candidate_plan"):
                replace(self.plan, **change)

    def test_hash_redaction_and_authority_stay_fail_closed(self):
        duplicate = prepare_m5_release_candidate_plan(
            self.review, planned_at=self.planned_at)
        later = prepare_m5_release_candidate_plan(
            self.review, planned_at=self.planned_at + timedelta(seconds=1))
        self.assertEqual(self.plan.plan_sha256, duplicate.plan_sha256)
        self.assertNotEqual(self.plan.plan_sha256, later.plan_sha256)
        self.assertEqual(len(self.plan.plan_sha256), 64)
        summary = self.plan.public_summary()
        for key in (
                "founder_response_recorded",
                "milestone_acceptance_recorded",
                "deployment_authorized",
                "private_data_authorized",
                "release_authorized",
                "real_money_authorized"):
            self.assertFalse(summary[key])
        payload = json.dumps(summary).lower()
        for forbidden in (
                "m4_review_sha256", "plan_sha256", "account_id",
                "credential", "token", "secret", "source_uri", "holding",
                "symbol", "strike", "reserved_cash",
                "gross_cumulative_return"):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
