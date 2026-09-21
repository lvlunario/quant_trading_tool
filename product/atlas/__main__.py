"""Run Atlas local research and normalized reconciliation commands."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from .adapters import NormalizedJsonAdapter
from .audit import ReplayLedger, source_sha256
from .ingestion import reconcile_envelope
from .risk import snapshot_report, standard_option_payoff


def main():
    parser = argparse.ArgumentParser(description="Atlas research kernel; no live trading")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--research-demo", action="store_true")
    source.add_argument("--broker-demo", action="store_true",
                        help="invented broker-shaped mapping; not Fidelity-compatible")
    source.add_argument("--synthetic-csv-demo", type=Path,
                        help="invented synthetic CSV only; not a broker/Fidelity import")
    source.add_argument("--preview-server", action="store_true",
                        help="localhost-only synthetic Options Lab")
    source.add_argument("--snapshot", type=Path)
    source.add_argument("--reconcile", type=Path,
                        help="versioned normalized JSON; not a broker CSV")
    parser.add_argument("--ledger", type=Path,
                        help="private local SQLite replay ledger; only with --reconcile")
    parser.add_argument("--preview-port", type=int,
                        help="localhost port 1024-65535; only with --preview-server")
    args = parser.parse_args()
    try:
        if args.ledger and not args.reconcile:
            raise ValueError('ledger_requires_reconcile')
        if args.preview_port is not None and not args.preview_server:
            raise ValueError('preview_port_requires_preview_server')
        if args.preview_server:
            from .web_preview import serve_preview
            serve_preview(args.preview_port if args.preview_port is not None else 8765)
            return 0
        elif args.broker_demo:
            from .broker_mapping import map_synthetic_broker_export

            now = datetime.now(timezone.utc)
            payload = {
                'schema_version': 1, 'mode': 'synthetic', 'currency': 'USD',
                'source_type': 'broker_mapping_synthetic',
                'source_id': 'SRC_BROKERDEMO1', 'as_of': now.isoformat(),
                'expected_totals': {'ALPHA': '100'},
                'rows': [
                    {'account_key': 'ALPHA', 'row_type': 'EQUITY', 'ticker': 'DEMO',
                     'quantity': '2.5', 'price': '10', 'market_value': '25'},
                    {'account_key': 'ALPHA', 'row_type': 'CASH', 'ticker': '',
                     'quantity': '0', 'price': '0', 'market_value': '75'},
                ],
            }
            report = map_synthetic_broker_export(payload, now=now)
            report['data_notice'] = 'invented values only; no broker file or account access'
        elif args.synthetic_csv_demo:
            from .broker_mapping import parse_synthetic_delimited

            if args.synthetic_csv_demo.stat().st_size > 1_000_000:
                raise ValueError("Input exceeds 1 MB limit")
            source_bytes = args.synthetic_csv_demo.read_bytes()
            digest = source_sha256(source_bytes)
            now = datetime.now(timezone.utc)
            report = parse_synthetic_delimited(
                source_bytes, source_id=f'SRC_{digest[:16].upper()}',
                as_of=now.isoformat(), now=now)
            report['source_sha256'] = digest
            report['data_notice'] = (
                'invented synthetic fixture only; runtime timestamp; '
                'no broker file or account access')
        elif args.research_demo:
            from datetime import date, timedelta
            from .provenance import ObservationRecord, assess_research_input
            from .reference import DataRightsRecord, SecurityRecord

            now = datetime.now(timezone.utc)
            instrument_id, provider_id, dataset_id = ('INS_123456789ABC', 'PRV_12345678',
                                                       'DATA_12345678')
            observation = ObservationRecord(
                'OBS_123456789ABC', 'SER_123456789ABC', 0, instrument_id,
                provider_id, dataset_id, 'MET_SYNTHETIC_VALUE', now.date(),
                now - timedelta(days=2), now - timedelta(days=1),
                'https://example.test/synthetic/source', 'a' * 64, 'b' * 64,
                'atlas.synthetic@1.0.0')
            security = SecurityRecord(
                instrument_id, 'ISS_123456789ABC', 'Synthetic Issuer',
                'Synthetic Class A', 'XNAS', 'USD', 'common_stock', 'DEMO',
                date(2020, 1, 1), None, 'https://example.test/synthetic/security',
                now - timedelta(days=1))
            permission = DataRightsRecord(
                provider_id, dataset_id, 'verified', ('internal_research',),
                'https://example.test/synthetic/terms', 'c' * 64,
                now - timedelta(days=2), now + timedelta(days=30))
            result = assess_research_input(
                [observation], [security], [permission], series_id=observation.series_id,
                decision_at=now, use_case='internal_research', now=now)
            report = {'mode': 'synthetic', 'status': result.status,
                      'codes': list(result.codes), 'observation_id': result.observation_id,
                      'readiness': 'contract gates only; no real data or investment conclusion'}
        elif args.demo:
            snapshot = {"schema_version": 1, "mode": "synthetic", "currency": "USD",
                        "as_of": datetime.now(timezone.utc).isoformat(), "cash": "20000",
                        "positions": [{"symbol": "DEMO", "asset_type": "equity",
                                       "quantity": "100", "price": "100"}]}
            report = {"portfolio": snapshot_report(snapshot), "hypothetical_put": standard_option_payoff(
                strategy="cash_secured_put", contracts=1, strike="90", premium_per_share="2",
                terminal_price="60", available_cash="20000", fees="1")}
        elif args.snapshot:
            if args.snapshot.stat().st_size > 1_000_000:
                raise ValueError("Input exceeds 1 MB limit")
            report = snapshot_report(json.loads(args.snapshot.read_text()))
        else:
            if args.reconcile.stat().st_size > 1_000_000:
                raise ValueError("Input exceeds 1 MB limit")
            source_bytes = args.reconcile.read_bytes()
            payload = NormalizedJsonAdapter().normalize(source_bytes)
            report = reconcile_envelope(payload)
            report['source_sha256'] = source_sha256(source_bytes)
            report['replay_status'] = 'not_checked'
            if args.ledger:
                ledger_result = ReplayLedger(args.ledger).record(
                    source_id=report['source_id'], source_hash=report['source_sha256'],
                    outcome=report['status'])
                report['replay_status'] = ledger_result.status
                report['first_seen_at'] = ledger_result.first_seen_at
                if ledger_result.status == 'exact_replay':
                    report['publishable_row_count'] = 0
                    report['readiness'] = 'exact replay; do not publish positions again'
        print(json.dumps(report, indent=2))
        if report.get('status') == 'blocked':
            return 3
    except (ValueError, KeyError, TypeError, OSError) as error:
        # Do not echo raw account content or file paths into logs.
        parser.exit(2, f"Input rejected ({type(error).__name__}); see input contract.\n")


if __name__ == "__main__":
    sys.exit(main() or 0)
