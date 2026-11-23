from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from atlas.m4_checkpoint import M4CheckpointExecution
from atlas.m4_iteration_review import prepare_m4_iteration_review


class M4IterationReviewTests(unittest.TestCase):
    def setUp(self):
        self.executed_at = datetime(
            2026, 11, 15, 12, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(
            2026, 11, 16, 11, 30, tzinfo=timezone.utc)
        self.execution = M4CheckpointExecution(
            executed_at=self.executed_at,
            candidate_sha256="a" * 64,
        )
        self.review = prepare_m4_iteration_review(
            self.execution, reviewed_at=self.reviewed_at)

    def test_packet_is_on_date_and_not_a_completed_meeting(self):
        summary = self.review.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["scheduled_review_date"], summary["review_timing"]),
            ("review_packet", "blocked", "2026-11-16",
             "prepared_on_date"),
        )
        self.assertFalse(summary["meeting_completed"])
        self.assertFalse(summary["founder_response_recorded"])
        self.assertFalse(summary["decisions_approved"])

    def test_demo_and_planned_vs_shipped_preserve_reduced_scope(self):
        summary = self.review.public_summary()
        self.assertEqual(
            (summary["demo"]["private_criteria_ready"],
             summary["demo"]["private_criteria_required"],
             summary["demo"]["private_criteria_deferred"]),
            (0, 5, 5),
        )
        self.assertTrue(summary["demo"][
            "continue_local_synthetic_fallback"])
        self.assertEqual(
            [row["state"] for row in summary["planned_vs_shipped"]],
            ["reduced_scope_only", "blocked",
             "catch_up_required_without_backdating"],
        )

    def test_packet_has_exactly_three_unapproved_recommendations(self):
        summary = self.review.public_summary()
        self.assertEqual(summary["recommendation_count"], 3)
        self.assertEqual(
            [item["decision"] for item in summary["recommendations"]],
            [
                "adopt_reduced_local_synthetic_release_candidate",
                "defer_authenticated_private_milestone_until_controls_exist",
                "freeze_scope_for_stabilization_on_2026_11_28",
            ],
        )
        self.assertTrue(all(
            item["status"] == "recommend"
            for item in summary["recommendations"]))

    def test_timeline_and_dependencies_are_explicit(self):
        summary = self.review.public_summary()
        self.assertEqual(
            (summary["timeline"]["stabilization_date"],
             summary["timeline"]["days_to_stabilization"],
             summary["timeline"]["prototype_target_date"],
             summary["timeline"]["days_to_prototype_target"]),
            ("2026-11-28", 12, "2026-12-12", 26),
        )
        self.assertEqual(len(summary["dependencies"]), 5)
        self.assertIn("dated_public_evidence_catch_up",
                      summary["dependencies"])

    def test_early_wrong_or_pre_execution_input_fails_closed(self):
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_iteration_review_input"):
            prepare_m4_iteration_review({}, reviewed_at=self.reviewed_at)
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_iteration_review_input"):
            prepare_m4_iteration_review(
                self.execution,
                reviewed_at=self.executed_at - timedelta(seconds=1),
            )
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_iteration_review"):
            prepare_m4_iteration_review(
                self.execution,
                reviewed_at=datetime(
                    2026, 11, 15, 15, 0, tzinfo=timezone.utc),
            )

    def test_review_hash_redaction_and_authority_are_fail_closed(self):
        duplicate = prepare_m4_iteration_review(
            self.execution, reviewed_at=self.reviewed_at)
        later = prepare_m4_iteration_review(
            self.execution,
            reviewed_at=self.reviewed_at + timedelta(seconds=1),
        )
        self.assertEqual(self.review.review_sha256,
                         duplicate.review_sha256)
        self.assertNotEqual(self.review.review_sha256,
                            later.review_sha256)
        self.assertEqual(len(self.review.review_sha256), 64)
        for change in (
                {"meeting_completed": True},
                {"founder_response_recorded": True},
                {"decisions_approved": True},
                {"milestone_accepted": True},
                {"deployment_authorized": True},
                {"private_data_authorized": True},
                {"release_authorized": True},
                {"real_money_authorized": True}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m4_iteration_review"):
                replace(self.review, **change)
        payload = json.dumps(self.review.public_summary()).lower()
        for forbidden in (
                "execution_sha256", "review_sha256", "account_id",
                "credential", "token", "secret", "source_uri", "holding",
                "symbol", "strike", "reserved_cash",
                "gross_cumulative_return"):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
