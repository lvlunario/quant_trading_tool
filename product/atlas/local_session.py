"""Fail-closed request boundary for the localhost synthetic preview.

This module does not authenticate a person or create a durable session.  It
only constrains the lifetime, host, method and exact route of the existing
process-local read-only demonstration.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta


LOCAL_READ_ROUTES = (
    "/",
    "/overview",
    "/checklist",
    "/import-demo",
    "/m1-status",
    "/weekly-review",
    "/integrated-readiness",
    "/research-work-items",
    "/research-work-items/identity",
    "/research-work-items/source",
    "/research-work-items/rights",
)
LOCAL_HOSTS = ("127.0.0.1", "localhost")
DEFAULT_SESSION_SECONDS = 15 * 60
MAX_SESSION_SECONDS = 30 * 60


def _aware(value):
    return isinstance(value, datetime) and value.tzinfo is not None


@dataclass(frozen=True)
class LocalSessionBoundary:
    """A short-lived allowlist for one local preview process.

    The term ``session`` describes the lifetime of the local process boundary,
    not an authenticated user session.
    """

    issued_at: datetime
    expires_at: datetime
    read_routes: tuple[str, ...] = LOCAL_READ_ROUTES
    hosts: tuple[str, ...] = LOCAL_HOSTS
    schema_version: int = 1
    scope: str = "localhost_synthetic_read_only"

    def __post_init__(self):
        lifetime = (self.expires_at - self.issued_at).total_seconds() \
            if _aware(self.issued_at) and _aware(self.expires_at) else 0
        if (self.schema_version != 1 or
                not _aware(self.issued_at) or
                not _aware(self.expires_at) or
                not 0 < lifetime <= MAX_SESSION_SECONDS or
                self.read_routes != LOCAL_READ_ROUTES or
                self.hosts != LOCAL_HOSTS or
                self.scope != "localhost_synthetic_read_only"):
            raise ValueError("invalid_local_session_boundary")

    def public_summary(self):
        return {
            "schema_version": self.schema_version,
            "status": "local_request_boundary_defined",
            "scope": self.scope,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "lifetime_seconds": int(
                (self.expires_at - self.issued_at).total_seconds()),
            "read_route_count": len(self.read_routes),
            "host_count": len(self.hosts),
            "read_only": True,
            "process_local": True,
            "identity_verified": False,
            "authentication_implemented": False,
            "cookie_issued": False,
            "durable_session_store": False,
            "private_persistence_implemented": False,
            "release_authorized": False,
        }


@dataclass(frozen=True)
class LocalReadDecision:
    allowed: bool
    reason: str
    schema_version: int = 1

    def __post_init__(self):
        allowed_reasons = {
            "local_synthetic_read_allowed",
            "host_not_allowed",
            "method_not_allowed",
            "route_not_allowed",
            "session_not_current",
        }
        if (self.schema_version != 1 or
                self.reason not in allowed_reasons or
                self.allowed !=
                (self.reason == "local_synthetic_read_allowed")):
            raise ValueError("invalid_local_read_decision")

    def public_summary(self):
        return {
            "schema_version": self.schema_version,
            "status": "allowed" if self.allowed else "denied",
            "reason": self.reason,
            "identity_verified": False,
            "authentication_implemented": False,
            "private_persistence_implemented": False,
            "release_authorized": False,
        }


def build_local_session_boundary(*, issued_at, lifetime_seconds=DEFAULT_SESSION_SECONDS):
    """Create the fixed local policy; no user identity or credential is bound."""
    if (type(lifetime_seconds) is not int or
            not 0 < lifetime_seconds <= MAX_SESSION_SECONDS):
        raise ValueError("invalid_local_session_lifetime")
    if not _aware(issued_at):
        raise ValueError("invalid_local_session_boundary")
    return LocalSessionBoundary(
        issued_at=issued_at,
        expires_at=issued_at + timedelta(seconds=lifetime_seconds),
    )


def evaluate_local_read(boundary, *, host, method, target, observed_at):
    """Evaluate a request without promoting the result to authentication."""
    if not isinstance(boundary, LocalSessionBoundary) or not _aware(observed_at):
        raise ValueError("invalid_local_read_request")
    if not isinstance(host, str) or not isinstance(method, str) or \
            not isinstance(target, str):
        raise ValueError("invalid_local_read_request")
    hostname = host.split(":", 1)[0]
    if hostname not in boundary.hosts:
        reason = "host_not_allowed"
    elif method != "GET":
        reason = "method_not_allowed"
    elif target not in boundary.read_routes:
        reason = "route_not_allowed"
    elif not boundary.issued_at <= observed_at < boundary.expires_at:
        reason = "session_not_current"
    else:
        reason = "local_synthetic_read_allowed"
    return LocalReadDecision(
        allowed=reason == "local_synthetic_read_allowed",
        reason=reason,
    )
