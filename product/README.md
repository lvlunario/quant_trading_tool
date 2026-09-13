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
python -m atlas --reconcile /absolute/private/path/normalized-import.json
python -m atlas --reconcile /absolute/private/path/normalized-import.json \
  --ledger /absolute/private/path/import-audit.sqlite3
```

The demo uses invented `DEMO` shares and hypothetical prices. Output includes snapshot concentration and a put downside scenario. No market-data calls, account linking, order placement, or model recommendations exist yet. Keep any real input/output outside the repository, including GitHub issues and CI logs.

## Program manual

The `atlas.ingestion` interface and `--reconcile` command validate versioned normalized rows, produce per-row outcomes, and block publication when account totals or positions disagree. The optional private SQLite ledger records only an opaque source ID, exact-source SHA-256, outcome and first-seen time; it suppresses publication on exact replay. See [import contract](docs/IMPORT_CONTRACT.md). The implemented adapter accepts Atlas-normalized JSON only—it is not a Fidelity CSV parser.

- [Program, roles, approvals and deadlines](docs/PROGRAM.md)
- [Requirements and metric inventory](docs/REQUIREMENTS.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Research validation and quality](docs/QUALITY.md)
- [Security and real-money release gates](docs/SECURITY.md)
- [Commercial and financing readiness](docs/COMMERCIAL.md)
- [Backlog and decisions](docs/BACKLOG.md)
- [Daily evidence logs](docs/daily/)

The root `src/` quantum experiment is legacy research and is not imported by Atlas. Its historical validation approach is not accepted performance evidence.
