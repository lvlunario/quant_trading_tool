from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from atlas.local_session import build_local_session_boundary
from atlas.private_environment_readiness import (
    M4_DEPENDENCIES,
    assess_private_environment_readiness,
)


class PrivateEnvironmentReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 11, 0, tzinfo=timezone.utc)
        self.local = build_local_session_boundary(issued_at=self.now)

    def assess(self, **changes):
        values = {"assessed_at": self.now, "local_session": self.local}
        values.update(changes)
        return assess_private_environment_readiness(**values)

    def test_exact_five_external_dependencies_remain_blocked(self):
        summary = self.assess().public_summary()
        self.assertEqual((summary["criteria_total"],
                          summary["criteria_ready"],
                          summary["criteria_blocked"]), (5, 0, 5))
        self.assertEqual(
            [item["name"] for item in summary["criteria"]],
            [item.name for item in M4_DEPENDENCIES],
        )
        self.assertTrue(all(not item["ready"]
                            for item in summary["criteria"]))

    def test_local_boundary_is_evidence_but_not_authentication(self):
        summary = self.assess().public_summary()
        self.assertEqual(summary["local_evidence"]["lifetime_seconds"], 900)
        self.assertTrue(summary["local_evidence"]
                        ["short_lived_request_boundary"])
        self.assertFalse(summary["local_evidence"]["identity_verified"])
        self.assertFalse(summary["local_evidence"]
                         ["authentication_implemented"])

    def test_private_release_and_real_money_capabilities_stay_false(self):
        summary = self.assess().public_summary()
        for key in ("milestone_acceptance_recorded", "release_authorized",
                    "deployment_authorized", "private_data_authorized",
                    "real_money_authorized"):
            self.assertFalse(summary[key])
        self.assertTrue(summary["capabilities"]["read_only"])
        for key, value in summary["capabilities"].items():
            if key != "read_only":
                self.assertFalse(value)

    def test_expired_future_or_naive_assessment_fails_closed(self):
        expired = build_local_session_boundary(
            issued_at=self.now - timedelta(minutes=16))
        for values in (
                {"local_session": expired},
                {"assessed_at": self.local.expires_at},
                {"assessed_at": datetime(2026, 11, 10, 11, 0)}):
            with self.subTest(values=values), self.assertRaisesRegex(
                    ValueError, "invalid_private_environment_readiness"):
                self.assess(**values)

    def test_dependency_or_policy_promotion_is_rejected(self):
        with self.assertRaisesRegex(
                ValueError, "invalid_private_environment_dependency"):
            replace(M4_DEPENDENCIES[0], ready=True)
        with self.assertRaisesRegex(
                ValueError, "invalid_private_environment_readiness"):
            replace(self.assess(), scope="hosted_production")

    def test_public_receipt_excludes_sensitive_or_financial_fields(self):
        payload = json.dumps(self.assess().public_summary()).lower()
        for forbidden in ("account_id", "credential", "token", "secret",
                          "source_uri", "holding", "symbol", "strike",
                          "return", "drawdown"):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
