"""Run Atlas local research and normalized reconciliation commands."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from .adapters import NormalizedJsonAdapter
from .audit import source_sha256
from .ingestion import reconcile_envelope
from .import_workflow import apply_replay_gate, synthetic_csv_report
from .risk import snapshot_report, standard_option_payoff


def main():
    parser = argparse.ArgumentParser(description="Atlas research kernel; no live trading")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--research-demo", action="store_true")
    source.add_argument("--source-demo", action="store_true",
                        help="fixed invented research source through all release gates")
    source.add_argument("--extractor-conformance-demo", action="store_true",
                        help="fixed synthetic extractor cases; no provider connection")
    source.add_argument("--provider-qualification-demo", action="store_true",
                        help="redacted protocol status; no provider data")
    source.add_argument("--m1-handoff", action="store_true",
                        help="public-safe milestone handoff; no acceptance authority")
    source.add_argument("--watchlist-registry-demo", action="store_true",
                        help="dated public security identities; no prices or holdings")
    source.add_argument("--source-catalog-demo", action="store_true",
                        help="public source candidates; metrics remain unavailable")
    source.add_argument("--source-rights-demo", action="store_true",
                        help="rights review plan; retrieval remains disabled")
    source.add_argument("--rights-evidence-demo", action="store_true",
                        help="reviewed terms evidence status; no retrieval authority")
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
                        help="private SQLite replay ledger; with --reconcile or --synthetic-csv-demo")
    parser.add_argument("--preview-port", type=int,
                        help="localhost port 1024-65535; only with --preview-server")
    args = parser.parse_args()
    try:
        if args.ledger and not (args.reconcile or args.synthetic_csv_demo):
            raise ValueError('ledger_requires_import')
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
            if args.synthetic_csv_demo.stat().st_size > 1_000_000:
                raise ValueError("Input exceeds 1 MB limit")
            source_bytes = args.synthetic_csv_demo.read_bytes()
            report = synthetic_csv_report(source_bytes, ledger_path=args.ledger)
        elif args.extractor_conformance_demo:
            from .extractor_conformance import evaluate_synthetic_extractor

            fixture = (Path(__file__).parents[1] / 'fixtures' /
                       'synthetic-extractor-conformance.json')
            report = evaluate_synthetic_extractor(fixture.read_bytes())
        elif args.source_catalog_demo:
            from .source_catalog import load_public_source_catalog
            from .watchlist_registry import load_public_watchlist_registry

            fixtures = Path(__file__).parents[1] / 'fixtures'
            registry = load_public_watchlist_registry(
                (fixtures / 'public-watchlist-identities.json').read_bytes())
            report = load_public_source_catalog(
                (fixtures / 'public-research-sources.json').read_bytes(),
                registry).public_summary()
        elif args.source_rights_demo:
            from .source_catalog import load_public_source_catalog
            from .source_rights import load_source_rights_manifest
            from .watchlist_registry import load_public_watchlist_registry

            fixtures = Path(__file__).parents[1] / 'fixtures'
            registry = load_public_watchlist_registry(
                (fixtures / 'public-watchlist-identities.json').read_bytes())
            catalog = load_public_source_catalog(
                (fixtures / 'public-research-sources.json').read_bytes(), registry)
            report = load_source_rights_manifest(
                (fixtures / 'public-source-rights-review.json').read_bytes(),
                catalog).public_summary()
        elif args.rights_evidence_demo:
            from .rights_evidence import (
                assess_reviewed_rights, load_reviewed_rights_evidence,
            )
            from .source_catalog import load_public_source_catalog
            from .watchlist_registry import load_public_watchlist_registry

            fixtures = Path(__file__).parents[1] / 'fixtures'
            registry = load_public_watchlist_registry(
                (fixtures / 'public-watchlist-identities.json').read_bytes())
            catalog = load_public_source_catalog(
                (fixtures / 'public-research-sources.json').read_bytes(), registry)
            records = load_reviewed_rights_evidence(
                (fixtures / 'public-source-rights-evidence.json').read_bytes(),
                catalog)
            report = assess_reviewed_rights(catalog, records).public_summary()
        elif args.watchlist_registry_demo:
            from .watchlist_registry import load_public_watchlist_registry

            fixture = (Path(__file__).parents[1] / 'fixtures' /
                       'public-watchlist-identities.json')
            report = load_public_watchlist_registry(fixture.read_bytes()).public_summary()
        elif args.m1_handoff:
            from .conformance import m1_milestone_handoff

            report = m1_milestone_handoff()
        elif args.provider_qualification_demo:
            from .provider_qualification import (
                assess_provider_qualification,
                default_provider_qualification_policy,
            )

            report = assess_provider_qualification(
                default_provider_qualification_policy())
        elif args.source_demo:
            from .source_workflow import synthetic_source_report

            fixture = Path(__file__).parents[1] / 'fixtures' / 'synthetic-research-source.json'
            report = synthetic_source_report(fixture.read_bytes())
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
            apply_replay_gate(report, source_sha256(source_bytes), args.ledger)
        print(json.dumps(report, indent=2))
        if report.get('status') == 'blocked':
            return 3
    except (ValueError, KeyError, TypeError, OSError) as error:
        # Do not echo raw account content or file paths into logs.
        parser.exit(2, f"Input rejected ({type(error).__name__}); see input contract.\n")


if __name__ == "__main__":
    sys.exit(main() or 0)
