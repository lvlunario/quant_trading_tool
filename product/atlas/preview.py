"""Synthetic, fixed UX-preview model derived from the deterministic risk kernel."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from .metric_evidence import MetricPayload, assess_metric_input
from .metrics import MetricDefinition, MetricValue
from .provenance import ObservationRecord
from .receipts import import_receipt
from .reference import DataRightsRecord, SecurityRecord
from .risk import snapshot_report, standard_option_payoff


PREVIEW_AS_OF = datetime(2026, 9, 12, tzinfo=timezone.utc)


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
    research = assess_metric_input(
        metric_payload, [observation], [security], [rights],
        series_id='SER_DEMO12345678', decision_at=PREVIEW_AS_OF,
        use_case='internal_research', now=PREVIEW_AS_OF)
    if research.status != 'ready':
        raise AssertionError("Synthetic research trace is inconsistent")
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
            "model_status": "fixed synthetic values calculated by atlas.risk"}
