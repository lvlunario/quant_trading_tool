"""Immutable identity records for the preregistered synthetic experiment.

The registry binds exact invented inputs, configuration and a Git commit before
execution.  A separate receipt can later bind output bytes without interpreting
them or creating an investment-performance claim.  There is no persistence,
market data, portfolio data or order path in this module.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import re

from .synthetic_series import (
    GENERATOR_VERSION, SyntheticSeries, generate_bars, trailing_target_changes,
)


SCHEMA_VERSION = 1
PROTOCOL_VERSION = 'atlas.m3.synthetic@1.0.0'
_HEX_40 = re.compile(r'[0-9a-f]{40}')
_HEX_64 = re.compile(r'[0-9a-f]{64}')


def _digest(content: bytes) -> str:
    return sha256(content).hexdigest()


@dataclass(frozen=True)
class ExperimentConfig:
    instrument_id: str = 'DEMO'
    sessions: int = 200
    lookback_sessions: int = 20
    holdout_start: int = 160
    label_horizon_sessions: int = 5
    training_gap_sessions: int = 1
    comparator: str = 'buy_and_hold'
    initial_cash: Decimal = Decimal('100000')
    base_cost_bps_per_side: int = 10
    base_delay_sessions: int = 1
    adverse_cost_bps_per_side: int = 25
    adverse_delay_sessions: int = 2
    adverse_overlap_policy: str | None = None

    def __post_init__(self):
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{1,15}', self.instrument_id):
            raise ValueError('invalid_experiment_instrument')
        integer_fields = (
            self.sessions, self.lookback_sessions, self.holdout_start,
            self.label_horizon_sessions, self.training_gap_sessions,
            self.base_cost_bps_per_side, self.base_delay_sessions,
            self.adverse_cost_bps_per_side, self.adverse_delay_sessions)
        if any(type(value) is not int for value in integer_fields):
            raise ValueError('invalid_experiment_integer')
        if not (2 <= self.sessions <= 10000 and
                1 <= self.lookback_sessions < self.holdout_start < self.sessions and
                self.label_horizon_sessions >= 1 and
                0 <= self.training_gap_sessions < self.holdout_start and
                0 <= self.base_cost_bps_per_side <= 10000 and
                0 <= self.adverse_cost_bps_per_side <= 10000 and
                self.base_delay_sessions >= 1 and self.adverse_delay_sessions >= 1):
            raise ValueError('invalid_experiment_configuration')
        if self.comparator != 'buy_and_hold':
            raise ValueError('unsupported_experiment_comparator')
        if self.adverse_overlap_policy not in (None, 'fifo'):
            raise ValueError('unsupported_adverse_overlap_policy')
        if (not isinstance(self.initial_cash, Decimal) or
                not self.initial_cash.is_finite() or self.initial_cash <= 0):
            raise ValueError('invalid_experiment_initial_cash')

    def canonical_bytes(self) -> bytes:
        fields = (
            ('instrument_id', self.instrument_id),
            ('sessions', str(self.sessions)),
            ('lookback_sessions', str(self.lookback_sessions)),
            ('holdout_start', str(self.holdout_start)),
            ('label_horizon_sessions', str(self.label_horizon_sessions)),
            ('training_gap_sessions', str(self.training_gap_sessions)),
            ('comparator', self.comparator),
            ('initial_cash', format(self.initial_cash.normalize(), 'f')),
            ('base_cost_bps_per_side', str(self.base_cost_bps_per_side)),
            ('base_delay_sessions', str(self.base_delay_sessions)),
            ('adverse_cost_bps_per_side', str(self.adverse_cost_bps_per_side)),
            ('adverse_delay_sessions', str(self.adverse_delay_sessions)),
        )
        content = ''.join(f'{name}={value}\n' for name, value in fields)
        if self.adverse_overlap_policy is not None:
            content += f'adverse_overlap_policy={self.adverse_overlap_policy}\n'
        return content.encode('ascii')

    @property
    def config_sha256(self) -> str:
        return _digest(self.canonical_bytes())


def canonical_series_bytes(series: SyntheticSeries) -> bytes:
    """Serialize only controlled invented-series fields in a fixed order."""
    if not isinstance(series, SyntheticSeries):
        raise ValueError('invalid_experiment_series')
    if (series.synthetic_only is not True or series.holdout_inspected is not False or
            series.investment_performance_established is not False):
        raise ValueError('series_not_preregistration_safe')
    lines = [
        f'generator_version={series.generator_version}',
        f'seed={series.seed}',
        f'lookback_sessions={series.lookback_sessions}',
        'bars=session|open|close',
    ]
    lines.extend(
        f'{row.session}|{row.open_price}|{row.close_price}' for row in series.bars)
    lines.append('targets=decision_session|target_exposure')
    lines.extend(
        f'{row.decision_session}|{row.target_exposure}' for row in series.targets)
    return ('\n'.join(lines) + '\n').encode('ascii')


@dataclass(frozen=True)
class ExperimentManifest:
    experiment_id: str
    protocol_version: str
    code_commit_sha: str
    generator_version: str
    config_sha256: str
    input_sha256: str
    schema_version: int = SCHEMA_VERSION
    status: str = 'preregistered'
    output_sha256: None = None
    synthetic_only: bool = True
    holdout_inspected: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{7,63}', self.experiment_id):
            raise ValueError('invalid_experiment_id')
        if self.protocol_version != PROTOCOL_VERSION:
            raise ValueError('unsupported_experiment_protocol')
        if _HEX_40.fullmatch(self.code_commit_sha) is None:
            raise ValueError('invalid_experiment_code_commit')
        if not re.fullmatch(r'atlas\.[a-z0-9_.-]+@[0-9]+\.[0-9]+\.[0-9]+',
                            self.generator_version):
            raise ValueError('invalid_experiment_generator')
        if any(_HEX_64.fullmatch(value) is None for value in
               (self.config_sha256, self.input_sha256)):
            raise ValueError('invalid_experiment_hash')
        if (self.schema_version != SCHEMA_VERSION or self.status != 'preregistered' or
                self.output_sha256 is not None or self.synthetic_only is not True or
                self.holdout_inspected is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_preregistration_state')

    def canonical_bytes(self) -> bytes:
        fields = (
            ('schema_version', str(self.schema_version)),
            ('experiment_id', self.experiment_id),
            ('protocol_version', self.protocol_version),
            ('code_commit_sha', self.code_commit_sha),
            ('generator_version', self.generator_version),
            ('config_sha256', self.config_sha256),
            ('input_sha256', self.input_sha256),
            ('status', self.status),
            ('output_sha256', ''),
            ('synthetic_only', 'true'),
            ('holdout_inspected', 'false'),
            ('investment_performance_established', 'false'),
        )
        return ''.join(f'{name}={value}\n' for name, value in fields).encode('ascii')

    @property
    def manifest_sha256(self) -> str:
        return _digest(self.canonical_bytes())


def register_experiment(
        series: SyntheticSeries, config: ExperimentConfig, *,
        experiment_id: str, code_commit_sha: str) -> ExperimentManifest:
    if not isinstance(series, SyntheticSeries):
        raise ValueError('invalid_experiment_series')
    if not isinstance(config, ExperimentConfig):
        raise ValueError('invalid_experiment_config')
    if (len(series.bars) != config.sessions or
            series.lookback_sessions != config.lookback_sessions or
            any(target.decision_session >= config.holdout_start
                for target in series.targets)):
        raise ValueError('experiment_series_config_mismatch')
    if series.generator_version != GENERATOR_VERSION:
        raise ValueError('unsupported_experiment_generator')
    expected_bars = generate_bars(seed=series.seed, sessions=config.sessions)
    expected_targets = trailing_target_changes(
        expected_bars, lookback_sessions=config.lookback_sessions,
        holdout_start=config.holdout_start)
    if series.bars != expected_bars or series.targets != expected_targets:
        raise ValueError('experiment_series_reproduction_mismatch')
    return ExperimentManifest(
        experiment_id, PROTOCOL_VERSION, code_commit_sha,
        series.generator_version, config.config_sha256,
        _digest(canonical_series_bytes(series)))


@dataclass(frozen=True)
class ExperimentOutputReceipt:
    manifest_sha256: str
    output_sha256: str
    output_bytes_count: int
    status: str = 'synthetic_plumbing_only'
    holdout_inspected: bool = False
    investment_performance_established: bool = False

    def __post_init__(self):
        if any(_HEX_64.fullmatch(value) is None for value in
               (self.manifest_sha256, self.output_sha256)):
            raise ValueError('invalid_output_binding_hash')
        if type(self.output_bytes_count) is not int or self.output_bytes_count < 1:
            raise ValueError('invalid_output_size')
        if (self.status != 'synthetic_plumbing_only' or
                self.holdout_inspected is not False or
                self.investment_performance_established is not False):
            raise ValueError('invalid_output_binding_state')


def bind_synthetic_output(
        manifest: ExperimentManifest, output: bytes) -> ExperimentOutputReceipt:
    """Hash opaque invented output; do not parse or validate its claims."""
    if not isinstance(manifest, ExperimentManifest):
        raise ValueError('invalid_output_manifest')
    if not isinstance(output, bytes) or not output:
        raise ValueError('invalid_output_bytes')
    return ExperimentOutputReceipt(
        manifest.manifest_sha256, _digest(output), len(output))
