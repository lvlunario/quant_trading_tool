"""Public-safe integration boundary for the localhost Atlas prototype."""
from dataclasses import dataclass
from datetime import datetime

from .options_acceptance import OptionsAcceptanceEvidence
from .receipts import ImportReceipt
from .weekly_report_readiness import WeeklyReportReadiness


@dataclass(frozen=True)
class IntegratedPrototypeReadiness:
    assessed_at: datetime
    portfolio: ImportReceipt
    research: WeeklyReportReadiness
    options: OptionsAcceptanceEvidence
    schema_version: int = 1
    scope: str = 'localhost_synthetic_read_only'

    def __post_init__(self):
        if (self.schema_version != 1 or
                not isinstance(self.assessed_at, datetime) or
                self.assessed_at.tzinfo is None or
                not isinstance(self.portfolio, ImportReceipt) or
                not isinstance(self.research, WeeklyReportReadiness) or
                not isinstance(self.options, OptionsAcceptanceEvidence) or
                self.research.assessed_at != self.assessed_at or
                self.portfolio.mode != 'synthetic' or
                self.portfolio.reconciliation != 'reconciled' or
                self.portfolio.rejected_rows != 0 or
                self.portfolio.decision != 'replay_check_required' or
                self.options.founder_acceptance_recorded is not False or
                self.options.real_chain_validated is not False or
                self.scope != 'localhost_synthetic_read_only'):
            raise ValueError('invalid_integrated_prototype_readiness')

    def public_summary(self) -> dict:
        research = self.research.public_summary()
        options = self.options.public_summary()
        return {
            'schema_version': self.schema_version,
            'status': 'synthetic_demo_ready_external_dependencies_blocked',
            'scope': self.scope,
            'assessed_at': self.assessed_at.isoformat(),
            'portfolio': {
                'status': 'synthetic_reconciliation_complete',
                'input_rows': self.portfolio.input_rows,
                'rejected_rows': self.portfolio.rejected_rows,
                'publishable_rows': self.portfolio.publishable_rows,
                'durable_replay_protection': False,
                'fidelity_validated': False,
            },
            'research': {
                'status': research['status'],
                'synthetic_section_count':
                    research['synthetic_shell']['section_count'],
                'universe_count':
                    research['sourced_report']['universe_count'],
                'stage_passed_counts':
                    research['sourced_report']['stage_passed_counts'],
                'sourced_statement_count': 0,
                'sourced_metric_count': 0,
                'publication_authorized': False,
            },
            'options': {
                'status': options['status'],
                'scenario_count': options['scenario_count'],
                'control_count': len(options['controls']),
                'real_chain_validated': False,
                'actionable_ranking_authorized': False,
            },
            'capabilities': {
                'read_only': True,
                'localhost_only': True,
                'authentication_implemented': False,
                'private_persistence_implemented': False,
                'network_retrieval_enabled': False,
                'order_path_enabled': False,
            },
            'external_dependencies': [
                'durable_private_replay_ledger',
                'representative_authorized_fidelity_export',
                'permitted_sourced_research_evidence',
                'fresh_option_chain_and_reconciled_collateral',
                'authentication_and_private_persistence',
                'browser_accessibility_and_owner_uat',
            ],
            'founder_acceptance_recorded': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'investment_performance_established': False,
        }


def compose_integrated_prototype_readiness(portfolio, research, options, *,
                                           assessed_at):
    """Compose three typed artifacts without promoting their blocked gates."""
    return IntegratedPrototypeReadiness(
        assessed_at=assessed_at,
        portfolio=portfolio,
        research=research,
        options=options,
    )
