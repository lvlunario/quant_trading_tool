"""Fail-closed M4 private-environment readiness receipt.

The receipt records missing control evidence.  It does not provision an
identity provider, storage, logging, recovery or a private deployment.
"""
from dataclasses import dataclass
from datetime import datetime

from .local_session import LocalSessionBoundary


_DEPENDENCY_BLOCKERS = (
    ("managed_authentication", "managed_identity_not_provisioned"),
    ("authorized_private_storage", "private_storage_not_provisioned"),
    ("recovery_restore_evidence", "restore_not_demonstrated"),
    ("redacted_operational_logging", "log_redaction_not_verified"),
    ("founder_uat", "founder_uat_not_recorded"),
)


def _aware(value):
    return isinstance(value, datetime) and value.tzinfo is not None


@dataclass(frozen=True)
class PrivateEnvironmentDependency:
    name: str
    blocker: str
    status: str = "blocked_external_evidence"
    ready: bool = False
    schema_version: int = 1

    def __post_init__(self):
        expected = dict(_DEPENDENCY_BLOCKERS).get(self.name)
        if (self.schema_version != 1 or
                expected != self.blocker or
                self.status != "blocked_external_evidence" or
                self.ready is not False):
            raise ValueError("invalid_private_environment_dependency")

    def public_summary(self):
        return {
            "name": self.name,
            "status": self.status,
            "blocker": self.blocker,
            "ready": self.ready,
        }


M4_DEPENDENCIES = tuple(
    PrivateEnvironmentDependency(name, blocker)
    for name, blocker in _DEPENDENCY_BLOCKERS
)


@dataclass(frozen=True)
class PrivateEnvironmentReadiness:
    assessed_at: datetime
    local_session: LocalSessionBoundary
    dependencies: tuple[PrivateEnvironmentDependency, ...] = M4_DEPENDENCIES
    schema_version: int = 1
    milestone: str = "M4_private_application"
    scope: str = "single_customer_private_read_only"

    def __post_init__(self):
        if (self.schema_version != 1 or
                not _aware(self.assessed_at) or
                not isinstance(self.local_session, LocalSessionBoundary) or
                not self.local_session.issued_at <= self.assessed_at <
                self.local_session.expires_at or
                self.dependencies != M4_DEPENDENCIES or
                self.milestone != "M4_private_application" or
                self.scope != "single_customer_private_read_only"):
            raise ValueError("invalid_private_environment_readiness")

    def public_summary(self):
        local = self.local_session.public_summary()
        return {
            "schema_version": self.schema_version,
            "status": "private_environment_blocked_external_evidence",
            "milestone": self.milestone,
            "scope": self.scope,
            "assessed_at": self.assessed_at.isoformat(),
            "local_evidence": {
                "short_lived_request_boundary": True,
                "lifetime_seconds": local["lifetime_seconds"],
                "localhost_only": True,
                "synthetic_only": True,
                "identity_verified": False,
                "authentication_implemented": False,
            },
            "criteria_total": len(self.dependencies),
            "criteria_ready": 0,
            "criteria_blocked": len(self.dependencies),
            "criteria": [item.public_summary()
                         for item in self.dependencies],
            "capabilities": {
                "read_only": True,
                "authentication_implemented": False,
                "private_storage_provisioned": False,
                "recovery_restore_verified": False,
                "log_redaction_verified": False,
                "founder_uat_recorded": False,
            },
            "milestone_acceptance_recorded": False,
            "release_authorized": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "real_money_authorized": False,
        }


def assess_private_environment_readiness(*, assessed_at, local_session):
    """Create the fixed blocked receipt without accepting promotion inputs."""
    return PrivateEnvironmentReadiness(
        assessed_at=assessed_at,
        local_session=local_session,
    )
