"""Founder decision record layered over immutable synthetic M3 evidence."""
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re

from .options_acceptance import OptionsAcceptanceEvidence
from .selection_freeze import SelectionFreezeCandidate


_HEX_64 = re.compile(r'[0-9a-f]{64}')


@dataclass(frozen=True)
class M3FounderDecisionRecord:
    decided_at: datetime
    freeze_candidate_sha256: str
    options_evidence_sha256: str
    schema_version: int = 1
    scope: str = 'synthetic_m3_governance_only'
    response: str = 'approve_all_presented_m3_decisions'
    selection_disposition: str = 'approved_freeze_without_tuning'
    holdout_disposition: str = 'authorized_once_after_selection_freeze'
    options_disposition: str = 'accepted_fixed_synthetic_scenarios'
    selection_frozen: bool = True
    holdout_authorized: bool = True
    options_acceptance_recorded: bool = True
    founder_response_recorded: bool = True
    holdout_inspected: bool = False
    milestone_accepted: bool = False
    release_authorized: bool = False
    real_data_validated: bool = False
    investment_performance_established: bool = False
    merge_authorized: bool = False
    trading_authorized: bool = False

    def __post_init__(self):
        if (self.schema_version != 1 or
                not isinstance(self.decided_at, datetime) or
                self.decided_at.tzinfo is None or
                _HEX_64.fullmatch(self.freeze_candidate_sha256 or '') is None or
                _HEX_64.fullmatch(self.options_evidence_sha256 or '') is None or
                self.scope != 'synthetic_m3_governance_only' or
                self.response != 'approve_all_presented_m3_decisions' or
                self.selection_disposition !=
                'approved_freeze_without_tuning' or
                self.holdout_disposition !=
                'authorized_once_after_selection_freeze' or
                self.options_disposition !=
                'accepted_fixed_synthetic_scenarios' or
                any(value is not True for value in (
                    self.selection_frozen, self.holdout_authorized,
                    self.options_acceptance_recorded,
                    self.founder_response_recorded)) or
                any(value is not False for value in (
                    self.holdout_inspected, self.milestone_accepted,
                    self.release_authorized, self.real_data_validated,
                    self.investment_performance_established,
                    self.merge_authorized, self.trading_authorized))):
            raise ValueError('invalid_m3_founder_decision_record')

    def public_summary(self) -> dict:
        return {
            'schema_version': self.schema_version,
            'status': 'holdout_authorized_pending_one_time_inspection',
            'scope': self.scope,
            'decided_at': self.decided_at.isoformat(),
            'decisions': [
                {
                    'decision': 'selection_freeze',
                    'disposition': self.selection_disposition,
                    'status': 'approved',
                },
                {
                    'decision': 'final_synthetic_holdout',
                    'disposition': self.holdout_disposition,
                    'status': 'authorized_not_inspected',
                },
                {
                    'decision': 'synthetic_options_scenarios',
                    'disposition': self.options_disposition,
                    'status': 'accepted_for_engineering_progression',
                },
            ],
            'm3_readiness': {
                'ready_count': 5,
                'required_count': 6,
                'remaining_criterion': 'final_holdout_receipt',
            },
            'sequence_guard': (
                'selection is frozen; execute at most one registered synthetic '
                'holdout inspection and bind its exact receipt'),
            'founder_response_recorded': True,
            'selection_frozen': True,
            'holdout_authorized': True,
            'holdout_inspected': False,
            'options_acceptance_recorded': True,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'real_data_validated': False,
            'investment_performance_established': False,
            'merge_authorized': False,
            'trading_authorized': False,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.public_summary(), sort_keys=True,
            separators=(',', ':')).encode('ascii')

    @property
    def decision_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


def record_m3_founder_decisions(freeze_candidate, options_evidence, *,
                                decided_at):
    """Record the three actual approvals without granting adjacent authority."""
    if (not isinstance(freeze_candidate, SelectionFreezeCandidate) or
            not isinstance(options_evidence, OptionsAcceptanceEvidence) or
            freeze_candidate.recommended_disposition !=
            'freeze_without_tuning' or
            freeze_candidate.selection_frozen is not False or
            freeze_candidate.holdout_authorized is not False or
            options_evidence.founder_acceptance_recorded is not False or
            options_evidence.real_chain_validated is not False):
        raise ValueError('invalid_m3_founder_decision_input')
    return M3FounderDecisionRecord(
        decided_at=decided_at,
        freeze_candidate_sha256=freeze_candidate.candidate_sha256,
        options_evidence_sha256=options_evidence.evidence_sha256,
    )
