"""Synthetic, fixed UX-preview model derived from the deterministic risk kernel."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .macro_vintages import MacroReleaseRecord, select_macro_vintage
from .metric_evidence import MetricPayload, assess_sourced_metric_input
from .metrics import MetricDefinition, MetricValue
from .provenance import ObservationRecord
from .provider_qualification import (assess_provider_qualification,
                                     default_provider_qualification_policy)
from .receipts import import_receipt
from .reference import DataRightsRecord, SecurityRecord
from .rights_evidence import (assess_reviewed_rights,
                              load_reviewed_rights_evidence)
from .risk import snapshot_report, standard_option_payoff
from .source_catalog import load_public_source_catalog
from .source_evidence import ResearchSourceRecord
from .source_workflow import synthetic_source_report
from .watchlist_registry import load_public_watchlist_registry


PREVIEW_AS_OF = datetime(2026, 9, 12, tzinfo=timezone.utc)
RIGHTS_PREVIEW_AS_OF = datetime(2026, 10, 4, 7, tzinfo=timezone.utc)


def public_rights_preview_trace():
    """Project only allowlisted reviewed-rights status into the preview."""
    fixtures = Path(__file__).parents[1] / 'fixtures'
    registry = load_public_watchlist_registry(
        (fixtures / 'public-watchlist-identities.json').read_bytes(),
        now=RIGHTS_PREVIEW_AS_OF)
    catalog = load_public_source_catalog(
        (fixtures / 'public-research-sources.json').read_bytes(), registry,
        now=RIGHTS_PREVIEW_AS_OF)
    evidence = load_reviewed_rights_evidence(
        (fixtures / 'public-source-rights-evidence.json').read_bytes(), catalog,
        now=RIGHTS_PREVIEW_AS_OF)
    summary = assess_reviewed_rights(
        catalog, evidence, at=RIGHTS_PREVIEW_AS_OF).public_summary()
    if (summary['status'] != 'blocked' or summary['rights_allowed_count'] != 0 or
            summary['technical_retrieval_status'] != 'disabled_separate_gate' or
            summary['release_authorized']):
        raise AssertionError('Public rights preview boundary is inconsistent')
    return {
        'status': summary['status'],
        'review_count': str(summary['review_count']),
        'rights_allowed_count': str(summary['rights_allowed_count']),
        'technical_retrieval_status': summary['technical_retrieval_status'],
        'release_authorized': str(summary['release_authorized']).lower(),
        **{f"{item['symbol'].lower()}_decision": item['decision']
           for item in summary['items']},
    }


def synthetic_import_receipts():
    """Return redacted receipt examples produced by the real receipt contract."""
    accepted = [
        {"row_number": 1, "status": "accepted"},
        {"row_number": 2, "status": "accepted"},
    ]
    reports = (
        {"mode": "synthetic", "status": "reconciled", "replay_status": "recorded",
         "outcomes": accepted, "publishable_row_count": 2, "errors": []},
        {"mode": "synthetic", "status": "blocked", "replay_status": "recorded",
         "outcomes": [accepted[0], {"row_number": 2, "status": "rejected"}],
         "publishable_row_count": 0, "errors": ["synthetic_invalid_row"]},
        {"mode": "synthetic", "status": "reconciled", "replay_status": "exact_replay",
         "outcomes": accepted, "publishable_row_count": 0, "errors": []},
        {"mode": "synthetic", "status": "reconciled", "replay_status": "not_checked",
         "outcomes": accepted, "publishable_row_count": 2, "errors": []},
    )
    receipts = [import_receipt(report).to_dict() for report in reports]
    return {receipt["decision"]: receipt for receipt in receipts}


def synthetic_preview_model():
    """Return the exact fixed values shown by the offline M0 preview.

    This is a regression contract, not a live quote, editable scenario, account
    snapshot, recommendation or promise that the HTML calls Python at runtime.
    """
    snapshot = {"schema_version": 1, "mode": "synthetic", "currency": "USD",
                "as_of": PREVIEW_AS_OF.isoformat(), "cash": "5000",
                "positions": [{"symbol": "DEMO", "asset_type": "equity",
                               "quantity": "100", "price": "50"}]}
    portfolio = snapshot_report(snapshot, now=PREVIEW_AS_OF)
    outcomes = {}
    for terminal in ("0", "48", "60"):
        outcomes[terminal] = standard_option_payoff(
            strategy="cash_secured_put", contracts=1, strike="50",
            premium_per_share="2", terminal_price=terminal, fees="0",
            available_cash="5000")
    if Decimal(outcomes["48"]["expiration_pnl"]) != 0:
        raise AssertionError("Synthetic preview breakeven is inconsistent")
    metric_definition = MetricDefinition(
        'MET_REVENUE', '1.0.0', 'Invented reported revenue', 'money', 'USD',
        'quarter', 'missing', 'synthetic.reported@1.0.0')
    metric_payload = MetricPayload(
        MetricValue(metric_definition, Decimal('123.40')),
        date(2026, 4, 1), date(2026, 6, 30))
    observation = ObservationRecord(
        'OBS_DEMO12345678', 'SER_DEMO12345678', 0, 'INS_DEMO12345678',
        'PRV_DEMO1234', 'DATA_DEMO1234', 'MET_REVENUE', date(2026, 6, 30),
        datetime(2026, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 9, 1, tzinfo=timezone.utc),
        'https://example.test/atlas/synthetic-revenue', 'a' * 64,
        metric_payload.payload_sha256, 'synthetic.reported@1.0.0')
    security = SecurityRecord(
        'INS_DEMO12345678', 'ISS_DEMO12345678', 'Synthetic Issuer',
        'Synthetic Class A', 'XNAS', 'USD', 'common_stock', 'DEMO',
        date(2020, 1, 1), None, 'https://example.test/atlas/synthetic-security',
        PREVIEW_AS_OF - timedelta(days=1))
    rights = DataRightsRecord(
        'PRV_DEMO1234', 'DATA_DEMO1234', 'verified', ('internal_research',),
        'https://example.test/atlas/synthetic-terms', 'b' * 64,
        PREVIEW_AS_OF - timedelta(days=30), PREVIEW_AS_OF + timedelta(days=30))
    source = ResearchSourceRecord(
        'DOC_DEMO12345678', observation.instrument_id, observation.provider_id,
        observation.dataset_id, 'regulator_filing', 'application/pdf',
        observation.available_at - timedelta(minutes=1), observation.available_at,
        observation.observed_at, observation.source_uri, observation.source_sha256)
    research = assess_sourced_metric_input(
        metric_payload, [observation], [security], [rights], source,
        series_id='SER_DEMO12345678', decision_at=PREVIEW_AS_OF,
        use_case='internal_research', now=PREVIEW_AS_OF)
    if research.status != 'ready':
        raise AssertionError("Synthetic research trace is inconsistent")
    fixture = (Path(__file__).parents[1] / 'fixtures' /
               'synthetic-research-source.json')
    workflow = synthetic_source_report(fixture.read_bytes(), now=PREVIEW_AS_OF)
    if (workflow['status'] != 'ready' or
            workflow['extraction']['status'] != 'ready'):
        raise AssertionError("Synthetic source workflow is inconsistent")

    macro_initial = MacroReleaseRecord(
        'MREL_DEMO12345678', 'MAC_DEMO12345678', 'PRV_MACRO1234',
        'DATA_MACRO1234', 'Invented monthly activity index', 'index', 'monthly',
        'seasonally_adjusted', date(2026, 7, 1), date(2026, 7, 31), 0,
        datetime(2026, 8, 5, 12, 30, tzinfo=timezone.utc),
        datetime(2026, 8, 5, 13, tzinfo=timezone.utc), Decimal('100.0'), None,
        'https://example.test/atlas/macro/initial', 'c' * 64,
        'synthetic.macro@1.0.0')
    macro_revised = MacroReleaseRecord(
        'MREL_DEMOABCDEF12', macro_initial.macro_series_id,
        macro_initial.provider_id, macro_initial.dataset_id, macro_initial.name,
        macro_initial.unit, macro_initial.frequency,
        macro_initial.seasonal_adjustment, macro_initial.period_start,
        macro_initial.period_end, 1,
        datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
        datetime(2026, 9, 5, 13, tzinfo=timezone.utc), Decimal('99.5'), None,
        'https://example.test/atlas/macro/revised', 'd' * 64,
        macro_initial.transform_version)
    macro_records = [macro_initial, macro_revised]
    macro_early = select_macro_vintage(
        macro_records, macro_series_id=macro_initial.macro_series_id,
        period_end=macro_initial.period_end,
        decision_at=datetime(2026, 8, 1, tzinfo=timezone.utc), now=PREVIEW_AS_OF)
    macro_late = select_macro_vintage(
        macro_records, macro_series_id=macro_initial.macro_series_id,
        period_end=macro_initial.period_end, decision_at=PREVIEW_AS_OF,
        now=PREVIEW_AS_OF)
    if macro_early.status != 'missing' or macro_late.status != 'selected':
        raise AssertionError("Synthetic macro vintage trace is inconsistent")
    qualification = assess_provider_qualification(
        default_provider_qualification_policy(), now=PREVIEW_AS_OF)
    if (qualification['status'] != 'blocked' or
            qualification['release_authorized']):
        raise AssertionError("Provider qualification boundary is inconsistent")
    return {"portfolio": portfolio, "put_outcomes": outcomes,
            "import_receipts": synthetic_import_receipts(),
            "research_trace": {
                "status": research.status,
                "value": str(research.payload.metric.value),
                "unit": research.payload.metric.definition.unit,
                "currency": research.payload.metric.definition.currency,
                "period_start": research.payload.period_start.isoformat(),
                "period_end": research.payload.period_end.isoformat(),
                "available_at": observation.available_at.isoformat(),
                "transform_version": observation.transform_version,
                "blocked_example": "identity_no_effective_instrument",
            },
            "source_trace": {
                "status": research.status,
                "document_id": source.document_id,
                "source_kind": source.source_kind,
                "provider_id": source.provider_id,
                "dataset_id": source.dataset_id,
                "available_at": source.available_at.isoformat(),
                "retrieved_at": source.retrieved_at.isoformat(),
                "binding": "exact_source_binding_passed",
            },
            "workflow_trace": {
                "status": workflow['status'],
                "source_sha256": workflow['source_sha256'],
                "metric_id": workflow['metric']['metric_id'],
                "value": workflow['metric']['value'],
                "extraction_status": workflow['extraction']['status'],
                "method": workflow['extraction']['method'],
                "review_status": workflow['extraction']['review_status'],
                "quality_code": workflow['extraction']['codes'][0],
                "release_code": workflow['codes'][0],
            },
            "macro_trace": {
                "series_id": macro_initial.macro_series_id,
                "period_end": macro_initial.period_end.isoformat(),
                "initial_value": str(macro_initial.value),
                "initial_available_at": macro_initial.available_at.isoformat(),
                "revised_value": str(macro_revised.value),
                "revised_available_at": macro_revised.available_at.isoformat(),
                "selected_revision": str(macro_late.revision),
                "selected_value": str(macro_late.value),
                "unavailable_code": macro_early.code,
            },
            "qualification_trace": {
                "status": qualification['status'],
                "evidence_scope": qualification['evidence_scope'],
                "document_count": str(qualification['document_count']),
                "field_check_count": str(qualification['field_check_count']),
                "exact_match_rate": (qualification['exact_match_rate'] or
                                     'unavailable'),
                "format_coverage_rate": (qualification['format_coverage_rate'] or
                                         'unavailable'),
                "missing_gate_count": str(len(qualification['codes'])),
                "primary_code": qualification['codes'][0],
                "release_authorized": str(
                    qualification['release_authorized']).lower(),
            },
            "rights_trace": public_rights_preview_trace(),
            "model_status": "fixed synthetic values calculated by atlas.risk"}
