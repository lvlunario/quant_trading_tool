"""Synthetic-only extractor conformance and sampling-policy evaluation."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re

from .source_workflow import synthetic_source_report


_TOP_KEYS = {
    'schema_version', 'mode', 'profile_id', 'provider_id', 'dataset_id',
    'extractor_version', 'expected_metric', 'sampling_policy', 'cases',
}
_METRIC_KEYS = {'metric_id', 'unit', 'currency', 'period'}
_POLICY_KEYS = {
    'minimum_cases', 'required_categories', 'max_false_accepts',
    'max_false_rejects', 'max_contract_mismatches',
}
_CASE_KEYS = {'case_id', 'category', 'source', 'expected'}
_EXPECTED_KEYS = {'status', 'code', 'value'}
_SAFE_CODE = re.compile(r'[a-z][a-z0-9_]{2,80}')


def _exact(value, keys, code):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(code)
    return value


def _identifier(pattern, value, code):
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError(code)


@dataclass(frozen=True)
class ExtractorSamplingPolicy:
    minimum_cases: int
    required_categories: tuple[str, ...]
    max_false_accepts: int
    max_false_rejects: int
    max_contract_mismatches: int

    def __post_init__(self):
        counts = (self.minimum_cases, self.max_false_accepts,
                  self.max_false_rejects, self.max_contract_mismatches)
        if (any(isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in counts) or self.minimum_cases < 1 or
                not isinstance(self.required_categories, tuple) or
                not self.required_categories or
                len(set(self.required_categories)) != len(self.required_categories) or
                any(re.fullmatch(r'[a-z][a-z0-9_]{2,30}', value) is None
                    for value in self.required_categories)):
            raise ValueError('invalid_extractor_sampling_policy')


@dataclass(frozen=True)
class ExtractorProfile:
    profile_id: str
    provider_id: str
    dataset_id: str
    extractor_version: str
    metric_id: str
    unit: str
    currency: str | None
    period: str
    policy: ExtractorSamplingPolicy

    def __post_init__(self):
        for pattern, value in (
            (r'XPF_[A-Z0-9]{12,32}', self.profile_id),
            (r'PRV_[A-Z0-9]{8,24}', self.provider_id),
            (r'DATA_[A-Z0-9]{8,32}', self.dataset_id),
            (r'[a-z][a-z0-9_.-]{0,39}@\d{1,6}\.\d{1,6}\.\d{1,6}',
             self.extractor_version),
            (r'MET_[A-Z0-9_]{4,40}', self.metric_id),
        ):
            _identifier(pattern, value, 'invalid_extractor_profile')
        monetary = self.unit in ('money', 'money_per_share')
        if (self.unit not in ('money', 'money_per_share', 'ratio', 'count') or
                self.period not in ('instant', 'quarter', 'annual', 'ttm') or
                (monetary and self.currency != 'USD') or
                (not monetary and self.currency is not None)):
            raise ValueError('invalid_extractor_metric_semantics')


def _load_manifest(manifest_bytes):
    if not isinstance(manifest_bytes, bytes) or not manifest_bytes:
        raise ValueError('invalid_conformance_manifest')
    try:
        raw = json.loads(manifest_bytes.decode('utf-8', errors='strict'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_conformance_manifest') from error
    manifest = _exact(raw, _TOP_KEYS, 'invalid_conformance_manifest_schema')
    if manifest['schema_version'] != 1 or manifest['mode'] != 'synthetic':
        raise ValueError('unsupported_conformance_manifest')
    metric = _exact(manifest['expected_metric'], _METRIC_KEYS,
                    'invalid_conformance_metric_schema')
    policy_raw = _exact(manifest['sampling_policy'], _POLICY_KEYS,
                        'invalid_conformance_policy_schema')
    categories = policy_raw['required_categories']
    if not isinstance(categories, list):
        raise ValueError('invalid_extractor_sampling_policy')
    policy = ExtractorSamplingPolicy(
        policy_raw['minimum_cases'], tuple(categories),
        policy_raw['max_false_accepts'], policy_raw['max_false_rejects'],
        policy_raw['max_contract_mismatches'])
    profile = ExtractorProfile(
        manifest['profile_id'], manifest['provider_id'], manifest['dataset_id'],
        manifest['extractor_version'], metric['metric_id'], metric['unit'],
        metric['currency'], metric['period'], policy)
    if (profile.provider_id, profile.dataset_id, profile.extractor_version) != (
            'PRV_DEMO1234', 'DATA_DEMO1234', 'atlas.synthetic_json@1.0.0'):
        raise ValueError('unsupported_synthetic_extractor_profile')
    cases = manifest['cases']
    if not isinstance(cases, list) or not cases or len(cases) > 1000:
        raise ValueError('invalid_conformance_cases')
    identifiers = []
    for case in cases:
        case = _exact(case, _CASE_KEYS, 'invalid_conformance_case_schema')
        _identifier(r'XCASE_[A-Z0-9]{8,32}', case['case_id'],
                    'invalid_conformance_case_id')
        identifiers.append(case['case_id'])
        if (not isinstance(case['category'], str) or
                re.fullmatch(r'[a-z][a-z0-9_]{2,30}', case['category']) is None or
                not isinstance(case['source'], dict)):
            raise ValueError('invalid_conformance_case')
        expected = _exact(case['expected'], _EXPECTED_KEYS,
                          'invalid_conformance_expected_schema')
        if (expected['status'] not in ('accepted', 'blocked') or
                not isinstance(expected['code'], str) or
                _SAFE_CODE.fullmatch(expected['code']) is None or
                (expected['value'] is not None and
                 not isinstance(expected['value'], str))):
            raise ValueError('invalid_conformance_expected')
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('duplicate_conformance_case_id')
    return profile, cases


def _run_case(case, profile, now):
    source_bytes = json.dumps(
        case['source'], sort_keys=True, separators=(',', ':'),
        ensure_ascii=True).encode('utf-8')
    try:
        result = synthetic_source_report(source_bytes, now=now)
        if result['status'] == 'ready':
            metric = result['metric']
            semantics = (metric['metric_id'], metric['unit'], metric['currency'],
                         metric['period'])
            expected_semantics = (profile.metric_id, profile.unit, profile.currency,
                                  profile.period)
            if semantics != expected_semantics:
                actual_status, code, value = ('blocked',
                    'conformance_metric_mismatch', None)
            else:
                actual_status, code, value = 'accepted', 'ready', metric['value']
        else:
            actual_status, code, value = 'blocked', result['codes'][0], None
    except (ValueError, KeyError, TypeError) as error:
        safe = str(error)
        code = safe if _SAFE_CODE.fullmatch(safe) else 'invalid_extractor_input'
        actual_status, value = 'blocked', None
    expected = case['expected']
    matched = (actual_status == expected['status'] and code == expected['code'] and
               value == expected['value'])
    return {
        'case_id': case['case_id'], 'category': case['category'],
        'expected_status': expected['status'], 'actual_status': actual_status,
        'code': code, 'matched': matched,
    }


def evaluate_synthetic_extractor(manifest_bytes, *, now=None):
    """Evaluate fixed invented cases; return classifications without source data."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid_conformance_time')
    profile, cases = _load_manifest(manifest_bytes)
    outcomes = [_run_case(case, profile, now) for case in cases]
    false_accepts = sum(outcome['expected_status'] == 'blocked' and
                        outcome['actual_status'] == 'accepted' for outcome in outcomes)
    false_rejects = sum(outcome['expected_status'] == 'accepted' and
                        outcome['actual_status'] == 'blocked' for outcome in outcomes)
    contract_mismatches = sum(not outcome['matched'] and not (
        outcome['expected_status'] == 'blocked' and outcome['actual_status'] == 'accepted')
        and not (outcome['expected_status'] == 'accepted' and
                 outcome['actual_status'] == 'blocked') for outcome in outcomes)
    covered = tuple(sorted({outcome['category'] for outcome in outcomes}))
    missing_categories = tuple(sorted(set(profile.policy.required_categories) - set(covered)))
    codes = []
    if len(outcomes) < profile.policy.minimum_cases:
        codes.append('insufficient_case_count')
    if missing_categories:
        codes.append('missing_required_categories')
    if false_accepts > profile.policy.max_false_accepts:
        codes.append('false_accept_limit_exceeded')
    if false_rejects > profile.policy.max_false_rejects:
        codes.append('false_reject_limit_exceeded')
    if contract_mismatches > profile.policy.max_contract_mismatches:
        codes.append('contract_mismatch_limit_exceeded')
    if not codes:
        codes.append('synthetic_conformance_passed')
    return {
        'schema_version': 1, 'mode': 'synthetic',
        'status': 'conformant_synthetic' if codes == ['synthetic_conformance_passed'] else 'blocked',
        'codes': codes, 'profile_id': profile.profile_id,
        'provider_id': profile.provider_id, 'dataset_id': profile.dataset_id,
        'extractor_version': profile.extractor_version,
        'case_count': len(outcomes),
        'matched_case_count': sum(outcome['matched'] for outcome in outcomes),
        'false_accept_count': false_accepts,
        'false_reject_count': false_rejects,
        'contract_mismatch_count': contract_mismatches,
        'category_coverage': list(covered),
        'missing_categories': list(missing_categories),
        'outcomes': outcomes,
        'qualification': ('synthetic contract only; no real provider compatibility '
                          'or measured production accuracy'),
    }
