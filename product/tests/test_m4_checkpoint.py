from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
import unittest

from atlas.integrated_readiness import compose_integrated_prototype_readiness
from atlas.local_session import build_local_session_boundary
from atlas.m2_acceptance_trace import M2AcceptanceTrace, M2GateStage
from atlas.m4_checkpoint import (
    assess_m4_checkpoint_candidate,
    execute_m4_checkpoint,
)
from atlas.options_acceptance import build_synthetic_options_acceptance_evidence
from atlas.private_environment_readiness import (
    assess_private_environment_readiness,
)
from atlas.receipts import ImportReceipt
from atlas.weekly_report_readiness import assess_weekly_report_readiness
from atlas.weekly_research_report import build_synthetic_weekly_research_report


class M4CheckpointCandidateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 13, 11, 30, tzinfo=timezone.utc)
        names = ("identity", "source_discovery", "rights_review",
                 "capture_authorization", "extraction", "metric_release")
        counts = (8, 8, 0, 0, 0, 0)
        blockers = ("identity_unresolved", "source_candidate_missing",
                    "rights_review_incomplete",
                    "capture_authorization_incomplete",
                    "no_authorized_source_bytes",
                    "no_verified_metric_evidence")
        trace = M2AcceptanceTrace(
            self.now, 9,
            tuple(M2GateStage(name, count, 9 - count, blocker)
                  for name, count, blocker in zip(names, counts, blockers)))
        weekly = build_synthetic_weekly_research_report(
            period_end=date(2026, 11, 13), generated_at=self.now)
        integrated = compose_integrated_prototype_readiness(
            ImportReceipt(
                1, "synthetic", "reconciled", "not_checked", 2, 0, 2,
                "replay_check_required"),
            assess_weekly_report_readiness(weekly, trace),
            build_synthetic_options_acceptance_evidence(),
            assessed_at=self.now,
        )
        private = assess_private_environment_readiness(
            assessed_at=self.now,
            local_session=build_local_session_boundary(issued_at=self.now),
        )
        self.integrated = integrated
        self.private = private
        self.candidate = assess_m4_checkpoint_candidate(integrated, private)

    def test_candidate_explicitly_defers_all_private_controls(self):
        summary = self.candidate.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["checkpoint_date"], summary["checkpoint_status"]),
            ("candidate", "blocked", "2026-11-14", "scheduled"),
        )
        self.assertEqual(
            (summary["private_environment"]["criteria_ready"],
             summary["private_environment"]["criteria_required"],
             summary["private_environment"]["criteria_deferred"]),
            (0, 5, 5),
        )
        self.assertTrue(all(
            item["recommendation"] == "recommend_defer"
            for item in summary["criteria"]))

    def test_local_synthetic_fallback_is_aggregate_not_acceptance(self):
        summary = self.candidate.public_summary()
        evidence = summary["aggregate_evidence"]
        self.assertEqual(evidence["portfolio_input_rows"], 2)
        self.assertEqual(evidence["research_stage_passed_counts"],
                         [8, 8, 0, 0, 0, 0])
        self.assertEqual((evidence["option_scenario_count"],
                          evidence["option_control_count"]), (2, 4))
        self.assertTrue(summary["continue_local_synthetic_fallback"])
        self.assertFalse(summary["founder_response_recorded"])
        self.assertFalse(summary["milestone_acceptance_recorded"])

    def test_manila_date_controls_checkpoint_state(self):
        cases = (
            ("2026-11-13T15:59:59+00:00", "scheduled", 1),
            ("2026-11-13T16:00:00+00:00", "due", 0),
            ("2026-11-14T15:59:59+00:00", "due", 0),
            ("2026-11-14T16:00:00+00:00", "elapsed", -1),
        )
        for timestamp, status, days in cases:
            with self.subTest(timestamp=timestamp):
                candidate = replace(
                    self.candidate, assessed_at=datetime.fromisoformat(timestamp))
                summary = candidate.public_summary()
                self.assertEqual(
                    (summary["checkpoint_status"],
                     summary["days_to_checkpoint"]), (status, days))

    def test_candidate_hash_is_deterministic(self):
        self.assertEqual(
            self.candidate.candidate_sha256,
            self.candidate.candidate_sha256,
        )
        self.assertEqual(len(self.candidate.candidate_sha256), 64)

    def test_authority_cannot_be_promoted(self):
        for change in (
                {"continue_local_synthetic_fallback": False},
                {"milestone_accepted": True},
                {"deployment_authorized": True},
                {"private_data_authorized": True},
                {"release_authorized": True},
                {"real_money_authorized": True}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m4_checkpoint_candidate"):
                replace(self.candidate, **change)

    def test_wrong_or_misaligned_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError,
                                    "invalid_m4_checkpoint_input"):
            assess_m4_checkpoint_candidate({}, self.private)
        later = self.now + timedelta(seconds=1)
        later_private = assess_private_environment_readiness(
            assessed_at=later,
            local_session=build_local_session_boundary(issued_at=later),
        )
        with self.assertRaisesRegex(ValueError,
                                    "invalid_m4_checkpoint_input"):
            assess_m4_checkpoint_candidate(self.integrated, later_private)
        other_integrated = replace(
            self.integrated,
            portfolio=replace(self.integrated.portfolio, input_rows=3,
                              publishable_rows=3),
        )
        with self.assertRaisesRegex(ValueError,
                                    "invalid_m4_checkpoint_input"):
            assess_m4_checkpoint_candidate(other_integrated, self.private)

    def test_public_candidate_excludes_private_and_financial_values(self):
        payload = json.dumps(self.candidate.public_summary()).lower()
        for forbidden in (
                "integrated_readiness_sha256", "private_environment_sha256",
                "candidate_sha256", "account_id", "credential", "token",
                "secret", "source_uri", "holding", "symbol", "strike",
                "reserved_cash", "gross_cumulative_return"):
            self.assertNotIn(forbidden, payload)
        for key in (
                "deployment_authorized", "private_data_authorized",
                "release_authorized", "real_money_authorized"):
            self.assertFalse(self.candidate.public_summary()[key])

    def test_due_checkpoint_executes_as_controlled_deferral(self):
        due = datetime(2026, 11, 14, 4, 0, tzinfo=timezone.utc)
        candidate = replace(self.candidate, assessed_at=due)
        execution = execute_m4_checkpoint(candidate, executed_at=due)
        summary = execution.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["checkpoint_status"], summary["days_after_checkpoint"]),
            ("executed", "blocked", "executed_due", 0),
        )
        self.assertTrue(summary["candidate_bound"])
        self.assertEqual(summary["disposition"],
                         "deferred_pending_explicit_founder_disposition")
        self.assertTrue(all(
            item["disposition"] == "deferred"
            for item in summary["criteria"]))

    def test_late_execution_is_explicit_and_never_backdated(self):
        candidate_time = datetime(
            2026, 11, 13, 12, 0, tzinfo=timezone.utc)
        execution_time = datetime(
            2026, 11, 15, 12, 0, tzinfo=timezone.utc)
        candidate = replace(self.candidate, assessed_at=candidate_time)
        summary = execute_m4_checkpoint(
            candidate, executed_at=execution_time).public_summary()
        self.assertEqual(
            (summary["checkpoint_status"],
             summary["days_after_checkpoint"], summary["executed_at"]),
            ("executed_late", 1, execution_time.isoformat()),
        )

    def test_checkpoint_cannot_execute_early_or_before_candidate(self):
        early = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_checkpoint_execution"):
            execute_m4_checkpoint(
                replace(self.candidate, assessed_at=early),
                executed_at=early,
            )
        due = datetime(2026, 11, 14, 4, 0, tzinfo=timezone.utc)
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_checkpoint_execution_input"):
            execute_m4_checkpoint(
                replace(self.candidate, assessed_at=due),
                executed_at=due - timedelta(seconds=1),
            )

    def test_execution_rejects_wrong_input_and_authority_promotion(self):
        due = datetime(2026, 11, 14, 4, 0, tzinfo=timezone.utc)
        with self.assertRaisesRegex(
                ValueError, "invalid_m4_checkpoint_execution_input"):
            execute_m4_checkpoint({}, executed_at=due)
        execution = execute_m4_checkpoint(
            replace(self.candidate, assessed_at=due), executed_at=due)
        for change in (
                {"continue_local_synthetic_fallback": False},
                {"founder_response_recorded": True},
                {"milestone_accepted": True},
                {"deployment_authorized": True},
                {"private_data_authorized": True},
                {"release_authorized": True},
                {"real_money_authorized": True}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m4_checkpoint_execution"):
                replace(execution, **change)

    def test_execution_hash_is_deterministic_and_public_output_is_redacted(self):
        due = datetime(2026, 11, 14, 4, 0, tzinfo=timezone.utc)
        execution = execute_m4_checkpoint(
            replace(self.candidate, assessed_at=due), executed_at=due)
        self.assertEqual(execution.execution_sha256,
                         execution.execution_sha256)
        self.assertEqual(len(execution.execution_sha256), 64)
        payload = json.dumps(execution.public_summary()).lower()
        for forbidden in (
                "candidate_sha256", "execution_sha256", "account_id",
                "credential", "token", "secret", "source_uri", "holding",
                "symbol", "strike", "reserved_cash",
                "gross_cumulative_return"):
            self.assertNotIn(forbidden, payload)
        for key in (
                "founder_response_recorded", "milestone_acceptance_recorded",
                "deployment_authorized", "private_data_authorized",
                "release_authorized", "real_money_authorized"):
            self.assertFalse(execution.public_summary()[key])


if __name__ == "__main__":
    unittest.main()
