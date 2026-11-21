"""Dated synthetic weekly research shell with explicit evidence semantics."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import re


_SECTION_ORDER = (
    'observation', 'hypothesis', 'counterargument', 'missing_evidence',
)
_SECTION_EVIDENCE = {
    'observation': ('synthetic_verified', 'synthetic_fixture'),
    'hypothesis': ('synthetic_assumption', 'not_applicable'),
    'counterargument': ('synthetic_assumption', 'not_applicable'),
    'missing_evidence': ('unavailable', 'missing'),
}
_STATEMENT_ID = re.compile(r'^SYN_[A-Z0-9]{8,32}$')


@dataclass(frozen=True)
class WeeklyResearchSection:
    statement_id: str
    section: str
    text: str
    as_of: date
    evidence_status: str
    source_status: str

    def __post_init__(self):
        expected = _SECTION_EVIDENCE.get(self.section)
        if (not _STATEMENT_ID.fullmatch(self.statement_id) or
                expected != (self.evidence_status, self.source_status) or
                not isinstance(self.as_of, date) or
                not isinstance(self.text, str) or
                not 1 <= len(self.text) <= 500 or
                self.text != self.text.strip() or
                any(ord(character) < 32 for character in self.text)):
            raise ValueError('invalid_weekly_research_section')

    def public_summary(self):
        return {
            'section': self.section,
            'statement_id': self.statement_id,
            'text': self.text,
            'as_of': self.as_of.isoformat(),
            'evidence_status': self.evidence_status,
            'source_status': self.source_status,
        }


@dataclass(frozen=True)
class WeeklyResearchReport:
    period_end: date
    generated_at: datetime
    sections: tuple[WeeklyResearchSection, ...]

    def __post_init__(self):
        if (not isinstance(self.period_end, date) or
                not isinstance(self.generated_at, datetime) or
                self.generated_at.tzinfo is None or
                self.generated_at.utcoffset() is None or
                self.period_end > self.generated_at.date() or
                tuple(item.section for item in self.sections) != _SECTION_ORDER or
                len({item.statement_id for item in self.sections}) != 4 or
                any(item.as_of != self.period_end for item in self.sections)):
            raise ValueError('invalid_weekly_research_report')

    def public_summary(self):
        return {
            'schema_version': 1,
            'mode': 'synthetic',
            'status': 'ready',
            'period_end': self.period_end.isoformat(),
            'generated_at': self.generated_at.isoformat(),
            'sections': [item.public_summary() for item in self.sections],
            'investment_conclusion': False,
            'milestone_acceptance_recorded': False,
            'release_authorized': False,
            'readiness': ('report structure only; invented statements contain no '
                          'real issuer, licensed data, portfolio conclusion or '
                          'investment recommendation'),
        }


def build_synthetic_weekly_research_report(*, period_end=None, generated_at=None):
    """Build the fixed invented report shell; no caller-provided content."""
    generated_at = generated_at or datetime.now(timezone.utc)
    if not isinstance(generated_at, datetime) or generated_at.tzinfo is None:
        raise ValueError('invalid_weekly_research_generated_at')
    period_end = period_end or generated_at.date()
    sections = (
        WeeklyResearchSection(
            'SYN_OBSERVATION01', 'observation',
            ('The invented fixture records a completed reporting period and a '
             'synthetic source timestamp.'),
            period_end, 'synthetic_verified', 'synthetic_fixture'),
        WeeklyResearchSection(
            'SYN_HYPOTHESIS01', 'hypothesis',
            ('If the invented operating trend persisted, research would test '
             'whether cash generation improved.'),
            period_end, 'synthetic_assumption', 'not_applicable'),
        WeeklyResearchSection(
            'SYN_COUNTERARGUMENT01', 'counterargument',
            ('The apparent trend could be a fixture artifact and has no external '
             'corroboration.'),
            period_end, 'synthetic_assumption', 'not_applicable'),
        WeeklyResearchSection(
            'SYN_MISSINGEVIDENCE01', 'missing_evidence',
            ('Current market data, audited filings, valuation inputs and portfolio '
             'relevance are unavailable.'),
            period_end, 'unavailable', 'missing'),
    )
    return WeeklyResearchReport(period_end, generated_at, sections)
