"""Public-safe M2 research work queue composed from existing evidence gates."""
from dataclasses import dataclass
from datetime import datetime

from .rights_evidence import RightsEvidenceReport
from .source_catalog import PublicSourceCatalog
from .watchlist_registry import WatchlistRegistry


_RIGHTS_CODES = frozenset({
    'missing_review_evidence', 'ambiguous_review_evidence',
    'expired_review_evidence', 'use_prohibited', 'counsel_review_required',
    'required_action_not_permitted', 'explicitly_permitted',
})


@dataclass(frozen=True)
class ResearchWorkItem:
    symbol: str
    status: str
    identity_status: str
    source_status: str
    rights_status: str
    extraction_status: str
    metric_status: str
    primary_blocker: str
    next_action: str

    def __post_init__(self):
        if (self.status != 'blocked' or
                self.identity_status not in ('resolved', 'unresolved') or
                self.source_status not in (
                    'catalogued_public_candidate', 'candidate_missing',
                    'not_applicable') or
                self.extraction_status not in ('not_attempted', 'not_applicable') or
                self.metric_status != 'unavailable' or
                not self.primary_blocker or not self.next_action):
            raise ValueError('invalid_research_work_item')

    def public_summary(self):
        return {
            'symbol': self.symbol,
            'status': self.status,
            'identity_status': self.identity_status,
            'source_status': self.source_status,
            'rights_status': self.rights_status,
            'extraction_status': self.extraction_status,
            'metric_status': self.metric_status,
            'primary_blocker': self.primary_blocker,
            'next_action': self.next_action,
        }


@dataclass(frozen=True)
class ResearchWorkQueue:
    as_of: datetime
    items: tuple[ResearchWorkItem, ...]

    def public_summary(self):
        catalogued = sum(
            item.source_status == 'catalogued_public_candidate'
            for item in self.items)
        rights_allowed = sum(
            item.rights_status == 'explicitly_permitted'
            for item in self.items)
        return {
            'schema_version': 1,
            'status': 'blocked',
            'as_of': self.as_of.isoformat(),
            'work_item_count': len(self.items),
            'blocked_count': len(self.items),
            'catalogued_source_count': catalogued,
            'rights_allowed_count': rights_allowed,
            'items': [item.public_summary() for item in self.items],
            'technical_retrieval_status': 'disabled_separate_gate',
            'release_authorized': False,
            'readiness': ('workflow gaps only; no source bytes, metric values, '
                          'recommendations or release authority'),
        }


def compose_research_work_queue(registry, catalog, rights_report):
    """Compose controlled gaps without promoting any source or metric state."""
    if (not isinstance(registry, WatchlistRegistry) or
            not isinstance(catalog, PublicSourceCatalog) or
            not isinstance(rights_report, RightsEvidenceReport) or
            catalog.as_of != registry.as_of or
            rights_report.assessed_at < catalog.as_of):
        raise ValueError('invalid_research_work_queue_input')

    resolved = {record.symbol for record in registry.records}
    blocked = {item['symbol'] for item in registry.blocked}
    candidates = {item.symbol for item in catalog.candidates}
    rights = {item.symbol: item for item in rights_report.items}
    if (not candidates <= resolved or set(rights) != candidates or
            resolved & blocked or len(resolved | blocked) != 9 or
            any(item.code not in _RIGHTS_CODES or
                item.rights_allowed != (item.code == 'explicitly_permitted')
                for item in rights_report.items)):
        raise ValueError('inconsistent_research_work_queue_input')

    items = []
    for record in registry.records:
        if record.symbol in candidates:
            decision = rights[record.symbol]
            next_action = ('capture_permitted_source_evidence'
                           if decision.rights_allowed else
                           'complete_terms_review')
            items.append(ResearchWorkItem(
                record.symbol, 'blocked', 'resolved',
                'catalogued_public_candidate', decision.code, 'not_attempted',
                'unavailable',
                ('source_evidence_missing' if decision.rights_allowed else
                 decision.code),
                next_action))
        else:
            items.append(ResearchWorkItem(
                record.symbol, 'blocked', 'resolved', 'candidate_missing',
                'not_assessed', 'not_attempted', 'unavailable',
                'source_candidate_missing', 'catalog_primary_source'))
    for item in registry.blocked:
        items.append(ResearchWorkItem(
            item['symbol'], 'blocked', 'unresolved', 'not_applicable',
            'not_assessed', 'not_applicable', 'unavailable',
            'identity_unresolved', 'resolve_authoritative_identity'))
    return ResearchWorkQueue(rights_report.assessed_at, tuple(items))
