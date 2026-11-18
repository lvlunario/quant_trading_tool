# M5 reduced release-candidate plan

Atlas must protect November 28–December 12 for stabilization. The November 18
plan therefore narrows the candidate before the freeze rather than treating the
missing private controls as finished work.

Run the public-safe plan:

```bash
python3 -m atlas --m5-release-candidate-plan-demo
```

The command exits `3` because the candidate is not frozen or accepted. It binds
the plan to the typed M4 asynchronous review, reports a 0/5 acceptance-gate
state and exposes no source, account, holding, credential or approval
identifiers.

## Proposed candidate scope

Only these already demonstrated local/synthetic workstreams are proposed:

1. synthetic portfolio import and reconciliation using checked-in invented
   fixtures;
2. the read-only research workbench using public metadata and synthetic report
   contracts;
3. deterministic hypothetical option scenarios and collateral controls; and
4. the weekly review and decision journal without an investment conclusion or
   release action.

Fidelity compatibility, managed authentication, authorized private storage,
private-record restore/deletion, licensed market/options data, completed data
rights reviews, production hosting and any order path remain deferred. The
plan cannot convert those deferrals into acceptance.

## Acceptance gates before the freeze decision

The November 28 decision remains blocked until the exact candidate has:

- a repeated fixture workflow from import through weekly review;
- an evidence-backed defect review with no unresolved critical calculation or
  privacy defect;
- reviewed paper-event history plus retry/restart behavior;
- an export/deletion/incident walkthrough with the stated recovery limits; and
- reviewed data-rights, security and operational runbook evidence.

The checked-in plan currently reports 0/5 ready. A passing unit-test suite is
necessary regression evidence, not proof that these human and environment
checks occurred.

## Stabilization policy

The policy is recorded now but remains inactive until an actual November 28
scope decision. After a freeze, allowed changes are limited to critical-defect
fixes, regression evidence, security evidence, acceptance evidence and
documentation corrections. New features, providers, unapproved private data,
production deployment and real-money order paths remain outside the candidate.

Founder acceptance, merge, deployment, private-data use and trading authority
are separate explicit gates. The date itself activates none of them.
