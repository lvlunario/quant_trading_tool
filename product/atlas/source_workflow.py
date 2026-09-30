"""Synthetic end-to-end source workflow with redacted output.

The workflow is intentionally fixed to invented evidence. It demonstrates the
same intake, provenance, identity, rights and metric-binding boundaries needed
by a future private adapter without fetching or retaining source content.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json

from .extraction_quality import ExtractionEvidence, assess_extraction_quality
from .metric_evidence import MetricPayload, assess_sourced_metric_input
from .metrics import MetricDefinition, MetricValue
from .provenance import ObservationRecord
from .reference import DataRightsRecord, SecurityRecord
from .source_intake import SourceIntakeRequest, intake_research_source


_TOP_LEVEL_KEYS = {'schema_version', 'mode', 'revision', 'metric'}
_METRIC_KEYS = {
    'metric_id', 'definition_version', 'formula', 'unit', 'currency', 'period',
    'null_policy', 'transform_version', 'value', 'missing_reason',
    'period_start', 'period_end',
}


def _exact_object(value, keys, code):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(code)
    return value


def _date(value):
    if not isinstance(value, str):
        raise ValueError('invalid_synthetic_source_date')
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError('invalid_synthetic_source_date') from error


def _metric_payload(raw):
    metric = _exact_object(raw, _METRIC_KEYS, 'invalid_synthetic_metric_schema')
    value = metric['value']
    if value is not None and not isinstance(value, str):
        raise ValueError('invalid_synthetic_metric_value')
    try:
        decimal_value = None if value is None else Decimal(value)
    except InvalidOperation as error:
        raise ValueError('invalid_synthetic_metric_value') from error
    definition = MetricDefinition(
        metric['metric_id'], metric['definition_version'], metric['formula'],
        metric['unit'], metric['currency'], metric['period'],
        metric['null_policy'], metric['transform_version'])
    return MetricPayload(
        MetricValue(definition, decimal_value, metric['missing_reason']),
        _date(metric['period_start']), _date(metric['period_end']))


def synthetic_source_report(source_bytes: bytes, *, now=None, rights=None):
    """Run invented JSON bytes through every release gate; return no raw content."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(source_bytes, bytes) or not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_synthetic_source_request')
    available_at = datetime(2026, 8, 1, 12, 5, tzinfo=timezone.utc)
    request = SourceIntakeRequest(
        'DOC_DEMO12345678', 'INS_DEMO12345678', 'PRV_DEMO1234',
        'DATA_DEMO1234', 'licensed_dataset', 'application/json',
        datetime(2026, 8, 1, 12, tzinfo=timezone.utc), available_at,
        'https://example.test/atlas/synthetic-research-source')
    default_rights = DataRightsRecord(
        request.provider_id, request.dataset_id, 'verified',
        ('internal_research',), 'https://example.test/atlas/synthetic-terms',
        'd' * 64, available_at - timedelta(days=30),
        datetime(2099, 1, 1, tzinfo=timezone.utc))
    permission_records = [default_rights] if rights is None else rights
    intake = intake_research_source(
        source_bytes, request, permission_records,
        use_case='internal_research', now=now)
    if intake.status != 'ready':
        return {
            'schema_version': 1, 'mode': 'synthetic', 'status': 'blocked',
            'codes': list(intake.codes), 'byte_count': intake.byte_count,
            'source_sha256': None, 'metric': None,
            'readiness': 'no metric released; synthetic contract demonstration only',
        }

    try:
        raw = json.loads(source_bytes.decode('utf-8', errors='strict'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_synthetic_source_json') from error
    record = _exact_object(raw, _TOP_LEVEL_KEYS, 'invalid_synthetic_source_schema')
    if record['schema_version'] != 1 or record['mode'] != 'synthetic':
        raise ValueError('unsupported_synthetic_source_contract')
    if isinstance(record['revision'], bool) or not isinstance(record['revision'], int):
        raise ValueError('invalid_synthetic_source_revision')

    payload = _metric_payload(record['metric'])
    source = intake.record
    extraction = ExtractionEvidence(
        'EXT_DEMO12345678', source.document_id,
        payload.metric.definition.metric_id, source.source_sha256,
        payload.payload_sha256, 'deterministic_parser',
        'atlas.synthetic_json@1.0.0', source.retrieved_at, 'not_required', None)
    quality = assess_extraction_quality(extraction, source, payload, now=now)
    extraction_report = {
        'status': quality.status, 'codes': list(quality.codes),
        'extraction_id': quality.extraction_id, 'method': extraction.method,
        'extractor_version': extraction.extractor_version,
        'review_status': extraction.review_status,
    }
    if quality.status != 'ready':
        return {
            'schema_version': 1, 'mode': 'synthetic', 'status': 'blocked',
            'codes': list(quality.codes), 'byte_count': intake.byte_count,
            'source_sha256': source.source_sha256, 'metric': None,
            'extraction': extraction_report,
            'readiness': 'no metric released; extraction quality blocked',
        }
    observation = ObservationRecord(
        'OBS_DEMO12345678', 'SER_DEMO12345678', record['revision'],
        source.instrument_id, source.provider_id, source.dataset_id,
        payload.metric.definition.metric_id, payload.period_end, source.available_at,
        source.retrieved_at, source.source_uri, source.source_sha256,
        payload.payload_sha256, payload.metric.definition.transform_version)
    security = SecurityRecord(
        source.instrument_id, 'ISS_DEMO12345678', 'Synthetic Issuer',
        'Synthetic Class A', 'XNAS', 'USD', 'common_stock', 'DEMO',
        date(2020, 1, 1), None, 'https://example.test/atlas/synthetic-security',
        source.retrieved_at)
    decision = assess_sourced_metric_input(
        payload, [observation], [security], permission_records, source,
        series_id=observation.series_id, decision_at=now,
        use_case='internal_research', now=now)
    metric = None
    if decision.payload is not None:
        definition = decision.payload.metric.definition
        metric = {
            'metric_id': definition.metric_id,
            'value': str(decision.payload.metric.value),
            'unit': definition.unit,
            'currency': definition.currency,
            'period': definition.period,
            'period_start': decision.payload.period_start.isoformat(),
            'period_end': decision.payload.period_end.isoformat(),
            'transform_version': definition.transform_version,
        }
    return {
        'schema_version': 1, 'mode': 'synthetic', 'status': decision.status,
        'codes': list(decision.codes), 'byte_count': intake.byte_count,
        'source_sha256': source.source_sha256, 'document_id': source.document_id,
        'observation_id': decision.observation_id, 'metric': metric,
        'extraction': extraction_report,
        'readiness': ('all synthetic source gates passed; no provider connection, '
                      'publisher authentication, accuracy claim or investment conclusion'),
    }
