# Security, privacy and real-money gates

## Immediate repository finding

The inherited public repository tracks a `.env` file. Its contents were not inspected or copied during foundation work, and no secret exposure is asserted without review. The owner should review it privately; if it contains real credentials, revoke/rotate them immediately and plan repository-history remediation. Removing a file from a new commit alone does not remove historical exposure. Atlas does not read that file. Track this as SEC-01; do not publish real account records or keys.

## Threat/control plan

| Threat | Required control before customer use | Verification |
|---|---|---|
| Account takeover | Managed authentication, MFA, short sessions, rate limits | Session/recovery abuse tests |
| Tenant data leakage | Server-side object authorization and tenant-scoped data | Cross-tenant negative tests |
| Credential leakage | Managed secrets, least privilege, log redaction, scanning | Scan and rotation drill |
| Bad/stale/poisoned data | Schema checks, source provenance, reconciliation, extraction conformance, private provider qualification and freshness gates | Corrupt/stale/provider-conflict, false-accept/reject and qualification-threshold fixtures |
| LLM fabrication or injection | Evidence-bound summaries, isolated tools, deterministic math | Adversarial-source test set |
| Duplicate jobs or actions | Idempotency keys, atomic state and audit history | Retry/crash/replay tests |
| Data loss/outage | Encrypted backups, restore rehearsal, incident runbooks | Measured restore and rollback |
| Unauthorized strategy change | Versioned policies, review, explicit approval | Audit trace and rejection tests |
| Malicious uploads | Size/type limits, parser isolation, no executable content | Fuzz/malformed-file cases |

Production controls above are planned, not implemented by the CLI. Collect only necessary data, use account aliases, encrypt in transit/at rest, define retention and deletion/export, avoid raw portfolio data in telemetry or general AI training, and disclose subprocessors. Obtain appropriate consent before ingestion.

The checked-in source-rights worksheet is a blank template containing public
source metadata and required field names only. Completed terms captures,
reviewer references and legal conclusions belong in the approved private
boundary and must not enter this repository, issues, PRs or CI output.
The localhost workbench may expose only aggregate task/check counts and blocked
gate states from that worksheet; it must not expose source addresses, document
or review identifiers, evidence-field names or completed evidence.
The source-capture receipt applies two-key control: a reviewed rights decision
and a separate exact-document technical approval. Approvals must be current,
bounded to one retrieval, capped at 5 MiB, restricted to HTML/PDF/JSON, and
forbid redirects and byte retention. Public receipts omit approval identifiers
and source/evidence details. The contract does not fetch or release data.
The workbench projection is an explicit allowlist of aggregate capture counts,
source-byte absence and the false release flag. Approval/document identifiers,
source/terms addresses, hashes and reviewer references are excluded.
The M2 acceptance trace narrows this further to aggregate gate counts. It emits
no symbols, source/review/approval identifiers, URLs, hashes, financial values
or recommendations, and it cannot accept source bytes or mark acceptance.
Its workbench projection uses only gate names, aggregate counts and controlled
blocker codes; it is read-only, fixed-cutoff and identical across filter routes.

The synthetic Options Lab preview is a temporary local development surface, not a hosted control. It binds only to IPv4 loopback, validates the Host/path/content type, requires a per-process form token, limits request size and field cardinality, suppresses request logs, returns no-store and restrictive browser headers, and persists nothing. Use invented values only and stop the process after review. These controls reduce accidental exposure; they do not provide authentication, TLS, tenant isolation, production CSRF assurance or permission to process portfolio data.

The normalized and synthetic-CSV import commands offer a narrow replay control: SHA-256 of exact source bytes plus an atomic SQLite uniqueness ledger containing no holdings. New ledger files are owner-only and permissive existing files are rejected. This helps prevent identical imports from being published twice; it does not encrypt data, authenticate users, provide tenant isolation, prove file authenticity, or make a hash anonymous. Store the ledger and its output only in a private location. Production requires a managed transactional audit store, key/access management, retention rules, backups and concurrency qualification.

## Release levels

- G0 Local synthetic research: allowed now; no customers, accounts or trades.
- G1 Private read-only prototype: requires verified import, consent, secure storage, authentication if hosted, founder acceptance and data rights.
- G2 Paying customers: requires independent security review, documented operations, support and privacy terms, jurisdiction/business-model legal review and validated marketing claims. Calling the product “research” does not itself settle legal classification.
- G3 Broker-assisted real-money actions: separate program requiring counsel, licensed/authorized counterparties as applicable, broker agreements, customer permissions, pre-trade checks, aggregate cash/share reservations, limits, kill switch, idempotent order IDs, execution reconciliation, incident response and controlled rollout.
- Custody/pooling customer funds: excluded from the three-month plan. Never commingle customer funds or represent this repository as authorized to custody assets.

U.S. SEC staff guidance highlights disclosure, suitable advice and compliance-program considerations for automated advisers: https://www.sec.gov/investment/im-guidance-2017-02.pdf (2017 guidance, reviewed September 12, 2026). This is a planning source, not a current legal clearance or a determination of registration obligations. Qualified counsel must review current U.S., Philippine and any other relevant rules based on entity, customer location, advice, compensation, discretion, custody, privacy and marketing model. No investor outreach or public performance claim is cleared by this document.
