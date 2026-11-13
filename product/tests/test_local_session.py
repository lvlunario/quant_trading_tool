from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from atlas.local_session import (LOCAL_READ_ROUTES,
                                 build_local_session_boundary,
                                 evaluate_local_read)


class LocalSessionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.issued_at = datetime(2026, 11, 7, 11, 0, tzinfo=timezone.utc)
        self.boundary = build_local_session_boundary(issued_at=self.issued_at)

    def decide(self, **changes):
        values = {
            "host": "127.0.0.1:8765",
            "method": "GET",
            "target": "/integrated-readiness",
            "observed_at": self.issued_at + timedelta(minutes=1),
        }
        values.update(changes)
        return evaluate_local_read(self.boundary, **values)

    def test_fixed_policy_is_short_lived_and_explicitly_not_authentication(self):
        report = self.boundary.public_summary()
        self.assertEqual(report["lifetime_seconds"], 900)
        self.assertEqual(report["read_route_count"], len(LOCAL_READ_ROUTES))
        self.assertTrue(report["read_only"])
        for key in ("identity_verified", "authentication_implemented",
                    "cookie_issued", "durable_session_store",
                    "private_persistence_implemented", "release_authorized"):
            self.assertFalse(report[key])

    def test_exact_local_get_is_allowed_without_identity_claim(self):
        report = self.decide().public_summary()
        self.assertEqual((report["status"], report["reason"]),
                         ("allowed", "local_synthetic_read_allowed"))
        self.assertFalse(report["identity_verified"])

    def test_nonlocal_host_mutation_and_query_variant_are_denied(self):
        cases = (
            ({"host": "example.com"}, "host_not_allowed"),
            ({"method": "POST"}, "method_not_allowed"),
            ({"target": "/integrated-readiness?mode=private"},
             "route_not_allowed"),
        )
        for changes, reason in cases:
            with self.subTest(reason=reason):
                decision = self.decide(**changes)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason, reason)

    def test_boundary_is_closed_before_issue_and_at_expiry(self):
        for observed_at in (
                self.issued_at - timedelta(microseconds=1),
                self.boundary.expires_at,
                self.boundary.expires_at + timedelta(seconds=1)):
            with self.subTest(observed_at=observed_at):
                decision = self.decide(observed_at=observed_at)
                self.assertEqual(decision.reason, "session_not_current")

    def test_lifetime_and_policy_cannot_be_broadened(self):
        for seconds in (0, 1801, True, "900"):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                build_local_session_boundary(
                    issued_at=self.issued_at, lifetime_seconds=seconds)
        with self.assertRaisesRegex(ValueError,
                                    "invalid_local_session_boundary"):
            replace(self.boundary,
                    read_routes=self.boundary.read_routes + ("/private",))

    def test_summary_excludes_tokens_identifiers_and_private_values(self):
        payload = json.dumps(self.boundary.public_summary()).lower()
        for forbidden in ("token", "cookie_value", "account", "instrument",
                          "source_uri", "session_id", "credential"):
            self.assertNotIn(forbidden, payload)

    def test_naive_or_wrongly_typed_requests_fail_closed(self):
        with self.assertRaises(ValueError):
            build_local_session_boundary(
                issued_at=datetime(2026, 11, 7, 11, 0))
        with self.assertRaisesRegex(ValueError, "invalid_local_read_request"):
            self.decide(observed_at=datetime(2026, 11, 7, 11, 1))
        with self.assertRaisesRegex(ValueError, "invalid_local_read_request"):
            self.decide(target=None)


if __name__ == "__main__":
    unittest.main()
