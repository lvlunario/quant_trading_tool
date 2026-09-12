# Security, privacy and real-money gates

## Immediate repository finding

The inherited public repository tracks a `.env` file. Its contents were not inspected or copied during foundation work, and no secret exposure is asserted without review. The owner should review it privately; if it contains real credentials, revoke/rotate them immediately and plan repository-history remediation. Removing a file from a new commit alone does not remove historical exposure. Atlas does not read that file. Track this as SEC-01; do not publish real account records or keys.

## Threat/control plan

| Threat | Required control before customer use | Verification |
|---|---|---|
| Account takeover | Managed authentication, MFA, short sessions, rate limits | Session/recovery abuse tests |
| Tenant data leakage | Server-side object authorization and tenant-scoped data | Cross-tenant negative tests |
| Credential leakage | Managed secrets, least privilege, log redaction, scanning | Scan and rotation drill |
| Bad/stale/poisoned data | Schema checks, source provenance, reconciliation and freshness gates | Corrupt/stale/provider-conflict fixtures |
| LLM fabrication or injection | Evidence-bound summaries, isolated tools, deterministic math | Adversarial-source test set |
| Duplicate jobs or actions | Idempotency keys, atomic state and audit history | Retry/crash/replay tests |
| Data loss/outage | Encrypted backups, restore rehearsal, incident runbooks | Measured restore and rollback |
| Unauthorized strategy change | Versioned policies, review, explicit approval | Audit trace and rejection tests |
| Malicious uploads | Size/type limits, parser isolation, no executable content | Fuzz/malformed-file cases |

Production controls above are planned, not implemented by the CLI. Collect only necessary data, use account aliases, encrypt in transit/at rest, define retention and deletion/export, avoid raw portfolio data in telemetry or general AI training, and disclose subprocessors. Obtain appropriate consent before ingestion.

## Release levels

- G0 Local synthetic research: allowed now; no customers, accounts or trades.
- G1 Private read-only prototype: requires verified import, consent, secure storage, authentication if hosted, founder acceptance and data rights.
- G2 Paying customers: requires independent security review, documented operations, support and privacy terms, jurisdiction/business-model legal review and validated marketing claims. Calling the product “research” does not itself settle legal classification.
- G3 Broker-assisted real-money actions: separate program requiring counsel, licensed/authorized counterparties as applicable, broker agreements, customer permissions, pre-trade checks, aggregate cash/share reservations, limits, kill switch, idempotent order IDs, execution reconciliation, incident response and controlled rollout.
- Custody/pooling customer funds: excluded from the three-month plan. Never commingle customer funds or represent this repository as authorized to custody assets.

U.S. SEC staff guidance highlights disclosure, suitable advice and compliance-program considerations for automated advisers: https://www.sec.gov/investment/im-guidance-2017-02.pdf (2017 guidance, reviewed September 12, 2026). This is a planning source, not a current legal clearance or a determination of registration obligations. Qualified counsel must review current U.S., Philippine and any other relevant rules based on entity, customer location, advice, compensation, discretion, custody, privacy and marketing model. No investor outreach or public performance claim is cleared by this document.
