from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from atlas.m5_regression_manifest import build_m5_regression_manifest
from atlas.m5_workflow_rehearsal import M5WorkflowRehearsal


class M5RegressionManifestTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 23, 11, 0, tzinfo=timezone.utc)
        self.rehearsal = M5WorkflowRehearsal(
            executed_at=self.now,
            plan_sha256="a" * 64,
            integrated_readiness_sha256="b" * 64,
        )
        self.product_root = Path(__file__).parents[1]
        self.manifest = build_m5_regression_manifest(
            self.rehearsal, self.product_root, generated_at=self.now)

    def _minimal_root(self, directory):
        root = Path(directory)
        for tree in ("atlas", "fixtures", "preview", "tests"):
            target = root / tree
            target.mkdir(parents=True)
            (target / "candidate.py").write_text(f"# {tree}\n")
        docs = root / "docs"
        docs.mkdir()
        for name in (
                "M5_RELEASE_CANDIDATE.md", "M5_DEFECT_REGISTER.md",
                "PROGRAM.md", "QUALITY.md", "SECURITY.md"):
            (docs / name).write_text(f"# {name}\n")
        return root

    def test_binds_all_safe_candidate_roots_and_runbooks(self):
        paths = [item.path for item in self.manifest.files]
        self.assertEqual(paths, sorted(paths))
        for prefix in ("atlas/", "fixtures/", "preview/", "tests/"):
            self.assertTrue(any(path.startswith(prefix) for path in paths))
        for path in (
                "docs/M5_RELEASE_CANDIDATE.md",
                "docs/M5_DEFECT_REGISTER.md", "docs/PROGRAM.md",
                "docs/QUALITY.md", "docs/SECURITY.md"):
            self.assertIn(path, paths)
        self.assertFalse(any(".env" in path for path in paths))

    def test_bundle_is_deterministic_and_content_sensitive(self):
        duplicate = build_m5_regression_manifest(
            self.rehearsal, self.product_root, generated_at=self.now)
        self.assertEqual(
            self.manifest.source_bundle_sha256,
            duplicate.source_bundle_sha256,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = self._minimal_root(directory)
            before = build_m5_regression_manifest(
                self.rehearsal, root, generated_at=self.now)
            (root / "atlas" / "candidate.py").write_text("# changed\n")
            after = build_m5_regression_manifest(
                self.rehearsal, root, generated_at=self.now)
            self.assertNotEqual(
                before.source_bundle_sha256, after.source_bundle_sha256)

    def test_public_contract_is_replayable_but_not_executed(self):
        summary = self.manifest.public_summary()
        self.assertEqual(
            (summary["receipt_state"], summary["status"],
             summary["regression_contract"]["command_count"]),
            ("pre_freeze_regression_manifest", "blocked", 3),
        )
        self.assertTrue(summary["source_bundle"]["content_addressed"])
        self.assertTrue(summary["regression_contract"]["ready_for_replay"])
        self.assertFalse(summary["regression_contract"]["execution_recorded"])
        self.assertEqual(
            [item["expected_exit"]
             for item in summary["regression_contract"]["commands"]],
            [0, 3, 3],
        )
        self.assertEqual(summary["candidate_gate"], {
            "ready": False,
            "blocker": "candidate_build_not_frozen",
            "manifest_only": True,
        })

    def test_wrong_inputs_times_and_authority_mutations_fail_closed(self):
        for rehearsal, generated_at in (
                ({}, self.now),
                (self.rehearsal, self.now.replace(tzinfo=None)),
                (self.rehearsal, self.now - timedelta(seconds=1))):
            with self.subTest(rehearsal=rehearsal,
                              generated_at=generated_at), self.assertRaisesRegex(
                    ValueError, "invalid_m5_regression_manifest_input"):
                build_m5_regression_manifest(
                    rehearsal, self.product_root, generated_at=generated_at)
        for change in (
                {"regression_executed": True},
                {"candidate_build_frozen": True},
                {"founder_response_recorded": True},
                {"milestone_accepted": True},
                {"deployment_authorized": True},
                {"private_data_authorized": True},
                {"release_authorized": True},
                {"real_money_authorized": True}):
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "invalid_m5_regression_manifest"):
                replace(self.manifest, **change)

    def test_symlinks_are_rejected_from_candidate_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._minimal_root(directory)
            (root / "atlas" / "linked.py").symlink_to(
                root / "atlas" / "candidate.py")
            with self.assertRaisesRegex(
                    ValueError, "invalid_m5_regression_manifest_file"):
                build_m5_regression_manifest(
                    self.rehearsal, root, generated_at=self.now)

    def test_public_summary_excludes_file_paths_and_authority(self):
        summary = self.manifest.public_summary()
        for key in (
                "founder_response_recorded",
                "milestone_acceptance_recorded", "deployment_authorized",
                "private_data_authorized", "release_authorized",
                "real_money_authorized",
                "investment_performance_established"):
            self.assertFalse(summary[key])
        payload = json.dumps(summary).lower()
        for forbidden in (
                "rehearsal_sha256", "manifest_sha256", "account_id",
                "credential", "token", "secret", "source_uri", "holding",
                "symbol", "strike", "reserved_cash",
                "gross_cumulative_return", "m5_regression_manifest.py"):
            self.assertNotIn(forbidden, payload)
class M5IterationReviewDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).parents[1] / "docs" / "reviews" /
                    "2026-11-23-M5-iteration-review.md").read_text()

    def test_review_contains_demo_qa_dependencies_and_three_decisions(self):
        text = self.text.lower()
        for marker in (
                "--m5-regression-manifest-demo", "planned versus shipped",
                "## qa", "## dependencies and forecast",
                "## three recommended decisions"):
            self.assertIn(marker, text)
        self.assertEqual(text.count("\n1. **") + text.count("\n2. **") +
                         text.count("\n3. **"), 3)

    def test_review_does_not_record_meeting_or_approval(self):
        text = self.text.lower()
        for marker in (
                "not a completed meeting", "recommendations, not approvals",
                "founder's actual response",
                "candidate freeze"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
