# Atlas — portfolio research and risk platform

Working name; trademark and domain availability are unverified. Target: a private, read-only research prototype by **December 12, 2026**. Current release: **0.1 foundation**, a local calculation kernel with synthetic demo. Not a customer-ready service.

Atlas will connect portfolio exposure, company fundamentals, economic conditions, systematic signals and option scenarios into an explainable weekly research process. Benchmark outperformance is a research hypothesis, never a product guarantee.

## Run the foundation

Use Python 3.11 or later. This kernel uses only the standard library; it does not need the experimental root requirements.

```bash
cd product
python -m unittest discover -s tests -v
python -m atlas --demo
python -m atlas --snapshot /absolute/private/path/snapshot.json
```

The demo uses invented `DEMO` shares and hypothetical prices. Output includes snapshot concentration and a put downside scenario. No market-data calls, account linking, order placement, or model recommendations exist yet. Keep any real input/output outside the repository, including GitHub issues and CI logs.

## Program manual

The new `atlas.ingestion.reconcile` Python interface validates synthetic normalized rows, produces a per-row outcome ledger, and blocks publication when account totals or positions disagree. See [import contract](docs/IMPORT_CONTRACT.md). It is not yet a Fidelity CSV parser or connected to the CLI.

- [Program, roles, approvals and deadlines](docs/PROGRAM.md)
- [Requirements and metric inventory](docs/REQUIREMENTS.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Research validation and quality](docs/QUALITY.md)
- [Security and real-money release gates](docs/SECURITY.md)
- [Commercial and financing readiness](docs/COMMERCIAL.md)
- [Backlog and decisions](docs/BACKLOG.md)
- [Daily evidence log](docs/daily/2026-09-12.md)

The root `src/` quantum experiment is legacy research and is not imported by Atlas. Its historical validation approach is not accepted performance evidence.
