"""Synthetic M3 evidence for aggregate option-collateral controls.

This module does not ingest a market-data chain or brokerage account.  It
proves, with fixed invented inputs, that Atlas reserves gross put cash and
covered-call shares across a batch and fails closed on stale chain evidence.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
import re

from .risk import amount


SCHEMA_VERSION = 1
CONTRACT_MULTIPLIER = 100
DEFAULT_MAX_CHAIN_AGE = timedelta(minutes=15)
_SCENARIO_ID = re.compile(r'SYNOPT_[A-Z0-9]{4,24}')
_INSTRUMENT_ID = re.compile(r'SYN_[A-Z0-9]{4,24}')


class OptionAcceptanceBlocked(ValueError):
    """Controlled fail-closed outcome; the message is a public-safe code."""


@dataclass(frozen=True)
class OptionScenarioRequest:
    scenario_id: str
    instrument_id: str
    strategy: str
    contracts: int
    strike: str
    fees: str
    chain_as_of: datetime
    source_mode: str = 'synthetic'

    def __post_init__(self):
        if (_SCENARIO_ID.fullmatch(self.scenario_id or '') is None or
                _INSTRUMENT_ID.fullmatch(self.instrument_id or '') is None or
                self.strategy not in ('cash_secured_put', 'covered_call') or
                type(self.contracts) is not int or self.contracts < 1 or
                self.source_mode != 'synthetic' or
                not isinstance(self.chain_as_of, datetime)):
            raise ValueError('invalid_option_scenario_request')
        strike, fees = amount(self.strike), amount(self.fees)
        if strike == 0:
            raise ValueError('invalid_option_scenario_request')
        object.__setattr__(self, 'strike', str(strike))
        object.__setattr__(self, 'fees', str(fees))

    @property
    def units(self) -> int:
        return self.contracts * CONTRACT_MULTIPLIER


@dataclass(frozen=True)
class CollateralReservationReceipt:
    scenario_count: int
    cash_secured_put_count: int
    covered_call_count: int
    reserved_cash: str
    reserved_shares: tuple[tuple[str, int], ...]
    source_mode: str = 'synthetic'
    schema_version: int = SCHEMA_VERSION
    current_chain_validated: bool = False
    actionable_ranking_authorized: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                self.source_mode != 'synthetic' or
                type(self.scenario_count) is not int or
                self.scenario_count < 1 or
                self.cash_secured_put_count + self.covered_call_count !=
                self.scenario_count or
                amount(self.reserved_cash) < 0 or
                tuple(sorted(self.reserved_shares)) != self.reserved_shares or
                any(_INSTRUMENT_ID.fullmatch(key) is None or
                    type(value) is not int or value < 1
                    for key, value in self.reserved_shares) or
                self.current_chain_validated is not False or
                self.actionable_ranking_authorized is not False):
            raise ValueError('invalid_collateral_reservation_receipt')

    def public_summary(self) -> dict:
        return {
            'schema_version': self.schema_version,
            'status': 'synthetic_reservation_complete',
            'source_mode': self.source_mode,
            'scenario_count': self.scenario_count,
            'cash_secured_put_count': self.cash_secured_put_count,
            'covered_call_count': self.covered_call_count,
            'share_reservation_instrument_count': len(self.reserved_shares),
            'gross_put_cash_reserved': self.cash_secured_put_count > 0,
            'covered_call_shares_reserved': self.covered_call_count > 0,
            'current_chain_validated': False,
            'actionable_ranking_authorized': False,
        }


def _whole_shares(value) -> int:
    shares = amount(value)
    if shares != shares.to_integral_value():
        raise ValueError('whole_unencumbered_shares_required')
    return int(shares)


def reserve_option_collateral(requests, *, available_cash,
                              unencumbered_shares, now,
                              max_chain_age=DEFAULT_MAX_CHAIN_AGE):
    """Reserve a synthetic batch atomically, rejecting aggregate double-use."""
    if (not isinstance(now, datetime) or now.tzinfo is None or
            not isinstance(max_chain_age, timedelta) or
            max_chain_age <= timedelta(0) or
            not isinstance(unencumbered_shares, dict)):
        raise ValueError('invalid_option_reservation_context')
    requests = tuple(requests)
    if not requests or any(not isinstance(item, OptionScenarioRequest)
                           for item in requests):
        raise ValueError('invalid_option_reservation_context')
    if len({item.scenario_id for item in requests}) != len(requests):
        raise ValueError('duplicate_option_scenario_id')

    cash_limit = amount(available_cash)
    share_limits = {}
    for instrument_id, shares in unencumbered_shares.items():
        if _INSTRUMENT_ID.fullmatch(instrument_id or '') is None:
            raise ValueError('invalid_option_reservation_context')
        share_limits[instrument_id] = _whole_shares(shares)

    reserved_cash = Decimal(0)
    reserved_shares = {}
    put_count = call_count = 0
    for request in requests:
        observed = request.chain_as_of
        if (observed.tzinfo is None or observed > now or
                now - observed > max_chain_age):
            raise OptionAcceptanceBlocked('chain_not_fresh')
        if request.strategy == 'cash_secured_put':
            put_count += 1
            # Premium is intentionally excluded from available collateral.
            reserve = amount(request.strike) * request.units + amount(request.fees)
            if reserved_cash + reserve > cash_limit:
                raise OptionAcceptanceBlocked(
                    'cash_collateral_double_use_or_shortfall')
            reserved_cash += reserve
        else:
            call_count += 1
            prior = reserved_shares.get(request.instrument_id, 0)
            required = prior + request.units
            if required > share_limits.get(request.instrument_id, 0):
                raise OptionAcceptanceBlocked(
                    'share_collateral_double_use_or_shortfall')
            reserved_shares[request.instrument_id] = required

    return CollateralReservationReceipt(
        scenario_count=len(requests),
        cash_secured_put_count=put_count,
        covered_call_count=call_count,
        reserved_cash=str(reserved_cash),
        reserved_shares=tuple(sorted(reserved_shares.items())),
    )


@dataclass(frozen=True)
class OptionsAcceptanceEvidence:
    reservation_receipt: CollateralReservationReceipt
    gross_put_cash_control_passed: bool
    put_cash_double_use_blocked: bool
    call_share_double_use_blocked: bool
    stale_chain_blocked: bool
    schema_version: int = SCHEMA_VERSION
    scope: str = 'synthetic_engineering_only'
    founder_acceptance_recorded: bool = False
    real_chain_validated: bool = False
    actionable_ranking_authorized: bool = False

    def __post_init__(self):
        if (self.schema_version != SCHEMA_VERSION or
                self.scope != 'synthetic_engineering_only' or
                not isinstance(self.reservation_receipt,
                               CollateralReservationReceipt) or
                any(value is not True for value in (
                    self.gross_put_cash_control_passed,
                    self.put_cash_double_use_blocked,
                    self.call_share_double_use_blocked,
                    self.stale_chain_blocked)) or
                self.founder_acceptance_recorded is not False or
                self.real_chain_validated is not False or
                self.actionable_ranking_authorized is not False):
            raise ValueError('invalid_options_acceptance_evidence')

    def public_summary(self) -> dict:
        return {
            'schema_version': self.schema_version,
            'status': 'ready_for_founder_scenario_review',
            'scope': self.scope,
            'scenario_count': self.reservation_receipt.scenario_count,
            'controls': {
                'gross_put_cash_reserved_without_premium': True,
                'put_cash_double_use_blocked': True,
                'call_share_double_use_blocked': True,
                'stale_chain_blocks_actionable_ranking': True,
            },
            'founder_acceptance_recorded': False,
            'real_chain_validated': False,
            'actionable_ranking_authorized': False,
            'limitations': [
                'fixed synthetic inputs only',
                'no broker buying power, margin, adjusted contracts or live chain',
                'no order path and no investment recommendation',
            ],
        }

    @property
    def evidence_sha256(self) -> str:
        payload = json.dumps(self.public_summary(), sort_keys=True,
                             separators=(',', ':')).encode('ascii')
        return sha256(payload).hexdigest()


def build_synthetic_options_acceptance_evidence():
    """Run fixed acceptance controls without inspecting any private data."""
    now = datetime(2026, 10, 29, 11, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(minutes=5)

    put = OptionScenarioRequest(
        'SYNOPT_PUT1', 'SYN_ALPHA', 'cash_secured_put', 1,
        '50', '1', fresh)
    call = OptionScenarioRequest(
        'SYNOPT_CALL1', 'SYN_BETA', 'covered_call', 1,
        '55', '1', fresh)
    receipt = reserve_option_collateral(
        (put, call), available_cash='5001',
        unencumbered_shares={'SYN_BETA': '100'}, now=now)

    def blocked(code, *requests, cash='5001', shares=None):
        try:
            reserve_option_collateral(
                requests, available_cash=cash,
                unencumbered_shares=shares or {}, now=now)
        except OptionAcceptanceBlocked as error:
            return str(error) == code
        return False

    second_put = OptionScenarioRequest(
        'SYNOPT_PUT2', 'SYN_GAMMA', 'cash_secured_put', 1,
        '50', '1', fresh)
    second_call = OptionScenarioRequest(
        'SYNOPT_CALL2', 'SYN_BETA', 'covered_call', 1,
        '55', '1', fresh)
    stale_put = OptionScenarioRequest(
        'SYNOPT_STALE1', 'SYN_ALPHA', 'cash_secured_put', 1,
        '50', '1', now - timedelta(minutes=16))
    return OptionsAcceptanceEvidence(
        reservation_receipt=receipt,
        gross_put_cash_control_passed=receipt.reserved_cash == '5001',
        put_cash_double_use_blocked=blocked(
            'cash_collateral_double_use_or_shortfall', put, second_put,
            cash='5001'),
        call_share_double_use_blocked=blocked(
            'share_collateral_double_use_or_shortfall', call, second_call,
            shares={'SYN_BETA': '100'}),
        stale_chain_blocked=blocked('chain_not_fresh', stale_put,
                                    cash='5001'),
    )


if __name__ == '__main__':
    evidence = build_synthetic_options_acceptance_evidence()
    output = evidence.public_summary()
    output['evidence_sha256'] = evidence.evidence_sha256
    print(json.dumps(output, sort_keys=True, separators=(',', ':')))
