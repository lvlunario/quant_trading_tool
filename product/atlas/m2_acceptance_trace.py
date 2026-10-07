"""Public-safe M2 gate trace; never records milestone acceptance.

The trace composes existing identity, source, rights and capture decisions. It
does not accept source bytes, extraction evidence or metric values, so those
later gates remain explicitly blocked in this version.
"""
from dataclasses import dataclass
from datetime import datetime

from .rights_evidence import RightsEvidenceReport
from .source_capture_authorization import SourceCaptureAuthorizationReceipt
from .source_catalog import PublicSourceCatalog
from .watchlist_registry import WatchlistRegistry


_STAGE_NAMES = (
    'identity', 'source_discovery', 'rights_review',
    'capture_authorization', 'extraction', 'metric_release',
)


@dataclass(frozen=True)
class M2GateStage:
    name: str
    passed_count: int
    blocked_count: int
    blocker: str

    def __post_init__(self):
        if (self.name not in _STAGE_NAMES or
                not isinstance(self.passed_count, int) or
                isinstance(self.passed_count, bool) or
                not isinstance(self.blocked_count, int) or
                isinstance(self.blocked_count, bool) or
                self.passed_count < 0 or self.blocked_count < 0 or
                not isinstance(self.blocker, str) or not self.blocker):
            raise ValueError('invalid_m2_gate_stage')

    def public_summary(self):
        return {
            'gate': self.name,
            'status': 'ready' if self.blocked_count == 0 else 'blocked',
            'passed_count': self.passed_count,
            'blocked_count': self.blocked_count,
            'blocker': self.blocker,
        }


@dataclass(frozen=True)
class M2AcceptanceTrace:
    assessed_at: datetime
    universe_count: int
    stages: tuple[M2GateStage, ...]

    def __post_init__(self):
        if (not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                not isinstance(self.universe_count, int) or
                isinstance(self.universe_count, bool) or
                self.universe_count <= 0 or
                tuple(stage.name for stage in self.stages) != _STAGE_NAMES or
                any(stage.passed_count + stage.blocked_count != self.universe_count
                    for stage in self.stages) or
                any(current.passed_count > previous.passed_count
                    for previous, current in zip(self.stages, self.stages[1:]))):
            raise ValueError('invalid_m2_acceptance_trace')

    def public_summary(self):
        return {
            'schema_version': 1,
            'status': 'blocked',
            'phase': 'M2 Sourced Research',
            'assessed_at': self.assessed_at.isoformat(),
            'universe_count': self.universe_count,
            'stages': [stage.public_summary() for stage in self.stages],
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'readiness': ('engineering gate trace only; no source bytes, extraction, '
                          'metric value, investment conclusion or founder acceptance'),
        }


def build_m2_acceptance_trace(registry, catalog, rights, capture):
    """Compose ordered counts and reject any inconsistent upstream state."""
    if (not isinstance(registry, WatchlistRegistry) or
            not isinstance(catalog, PublicSourceCatalog) or
            not isinstance(rights, RightsEvidenceReport) or
            not isinstance(capture, SourceCaptureAuthorizationReceipt) or
            catalog.as_of != registry.as_of or
            rights.assessed_at != capture.assessed_at or
            rights.assessed_at < catalog.as_of):
        raise ValueError('invalid_m2_acceptance_trace_input')

    resolved = {record.symbol for record in registry.records}
    blocked = {item['symbol'] for item in registry.blocked}
    source_symbols = {item.symbol for item in catalog.candidates}
    rights_symbols = tuple(item.symbol for item in rights.items)
    capture_symbols = tuple(item.symbol for item in capture.items)
    universe_count = len(resolved | blocked)
    rights_ready = sum(item.rights_allowed for item in rights.items)
    capture_ready = sum(item.capture_authorized for item in capture.items)
    if (resolved & blocked or source_symbols - resolved or
            universe_count != 9 or len(source_symbols) != 8 or
            rights_symbols != tuple(item.symbol for item in catalog.candidates) or
            capture_symbols != rights_symbols or
            any(capture_item.rights_allowed != rights_item.rights_allowed
                for capture_item, rights_item in zip(capture.items, rights.items)) or
            capture_ready > rights_ready):
        raise ValueError('inconsistent_m2_acceptance_trace_input')

    counts = (
        ('identity', len(resolved), 'identity_unresolved'),
        ('source_discovery', len(source_symbols), 'source_candidate_missing'),
        ('rights_review', rights_ready, 'rights_review_incomplete'),
        ('capture_authorization', capture_ready,
         'capture_authorization_incomplete'),
        ('extraction', 0, 'no_authorized_source_bytes'),
        ('metric_release', 0, 'no_verified_metric_evidence'),
    )
    stages = tuple(M2GateStage(name, passed, universe_count - passed, blocker)
                   for name, passed, blocker in counts)
    return M2AcceptanceTrace(capture.assessed_at, universe_count, stages)
