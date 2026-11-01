"""October 31 M3 checkpoint composed from immutable synthetic evidence."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .m3_milestone_readiness import M3MilestoneReadiness
from .options_acceptance import OptionsAcceptanceEvidence


M3_TARGET_DATE = date(2026, 10, 31)
_HEX_64 = re.compile(r'[0-9a-f]{64}')


@dataclass(frozen=True)
class M3Checkpoint:
    assessed_at: datetime
    readiness_sha256: str
    options_evidence_sha256: str
    target_date: date = M3_TARGET_DATE
    schema_version: int = 1
    scope: str = 'synthetic_engineering_only'
    protocol_controls_ready: bool = True
    options_controls_ready: bool = True
    selection_frozen: bool = False
    holdout_authorized: bool = False
    holdout_inspected: bool = False
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    release_authorized: bool = False
    real_data_validated: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if (self.schema_version != 1 or
                not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                self.target_date != M3_TARGET_DATE or
                _HEX_64.fullmatch(self.readiness_sha256 or '') is None or
                _HEX_64.fullmatch(self.options_evidence_sha256 or '') is None or
                self.scope != 'synthetic_engineering_only' or
                self.protocol_controls_ready is not True or
                self.options_controls_ready is not True or
                any(value is not False for value in (
                    self.selection_frozen, self.holdout_authorized,
                    self.holdout_inspected, self.founder_response_recorded,
                    self.milestone_accepted, self.release_authorized,
                    self.real_data_validated,
                    self.investment_performance_established))):
            raise ValueError('invalid_m3_checkpoint')

    def public_summary(self) -> dict:
        local_date = self.assessed_at.astimezone(
            ZoneInfo('Asia/Manila')).date()
        days_to_target = (self.target_date - local_date).days
        criteria = (
            ('registered_protocol', 'ready', 'none'),
            ('reproducible_validation', 'ready', 'none'),
            ('costs_and_benchmark', 'ready', 'none'),
            ('selection_freeze', 'blocked',
             'founder_selection_freeze_response_required'),
            ('final_holdout', 'blocked',
             'selection_freeze_and_holdout_authorization_required'),
            ('options_scenario_acceptance', 'blocked',
             'founder_scenario_review_required'),
        )
        return {
            'schema_version': self.schema_version,
            'status': 'acceptance_blocked',
            'phase': 'M3 Strategy laboratory',
            'scope': self.scope,
            'assessed_at': self.assessed_at.isoformat(),
            'target_date': self.target_date.isoformat(),
            'target_status': ('scheduled' if days_to_target > 0 else
                              'due' if days_to_target == 0 else 'elapsed'),
            'days_to_target': days_to_target,
            'criteria': [
                {'criterion': name, 'status': status, 'blocker': blocker}
                for name, status, blocker in criteria
            ],
            'ready_count': 3,
            'required_count': 6,
            'engineering_evidence': {
                'protocol_controls_ready': True,
                'options_collateral_and_freshness_controls_ready': True,
            },
            'decision_dependencies': [
                'founder_selection_freeze_response',
                'founder_holdout_authorization',
                'founder_options_scenario_review',
            ],
            'founder_response_recorded': False,
            'holdout_inspected': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'real_data_validated': False,
            'investment_performance_established': False,
            'recommendation': (
                'keep holdout sealed; record explicit founder decisions; '
                'continue to integrated private prototype without claiming M3 acceptance'),
        }

    @property
    def checkpoint_sha256(self) -> str:
        payload = json.dumps(self.public_summary(), sort_keys=True,
                             separators=(',', ':')).encode('ascii')
        return sha256(payload).hexdigest()


def assess_m3_checkpoint(readiness, options_evidence, *, assessed_at):
    if (not isinstance(readiness, M3MilestoneReadiness) or
            not isinstance(options_evidence, OptionsAcceptanceEvidence) or
            readiness.options_acceptance_ready is not False or
            options_evidence.founder_acceptance_recorded is not False):
        raise ValueError('invalid_m3_checkpoint_input')
    return M3Checkpoint(
        assessed_at=assessed_at,
        readiness_sha256=readiness.readiness_sha256,
        options_evidence_sha256=options_evidence.evidence_sha256,
    )
