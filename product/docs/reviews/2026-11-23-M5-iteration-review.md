# M5 asynchronous concept and iteration review — November 23, 2026

Prepared November 23, 2026 at 19:51 Asia/Manila.

**State: review packet prepared on date; M5 remains pre-freeze and blocked.**
This packet is not a completed meeting, founder response, decision approval,
candidate freeze, milestone acceptance, deployment approval or release.

## Demo

From `product/`:

```sh
python3 -m atlas --m5-regression-manifest-demo
```

Expected result: exit `3` with
`receipt_state=pre_freeze_regression_manifest`, `status=blocked`, four safe
coverage roots, five runbooks, one content-bundle digest and three ordered
replay commands. `execution_recorded=false`, the candidate gate remains
blocked and every authority flag remains false.

The manifest converts “run the latest code” into a content-addressed replay
contract. It does not execute the commands, inspect private data or establish
that the November 28 build exists.

## Planned versus shipped

| Planned by November 28 | Actually shipped | Review state |
|---|---|---|
| Exact candidate workflow and repeatable regression | Typed manifest binds code, fixtures, preview, tests and five runbooks | Reproducible pre-freeze identity; execution still pending |
| Authenticated private read-only application | Localhost synthetic workflow and 0/5 private-control receipt | Reduced scope only; authenticated milestone deferred |
| Current weekly public evidence | Separately dated November 21 primary-source packet finalized November 22 | Research workflow available; no recommendation or source-rights approval |

M3 synthetic engineering evidence remains 6/6 without milestone acceptance.
M4 remains deferred at 0/5 private controls. The November 28 candidate is not
frozen and all five M5 acceptance gates remain blocked.

## QA

- Nine direct manifest, CLI and review-document checks pass.
- Full local suite: 523 tests passed.
- The regression manifest command returns the expected blocked exit `3` and
  emits no per-file paths, account data, credentials or performance fields.
- Hosted exact-head verification is pending publication of this increment.
- Direct Chromium browser/device QA remains open; the November 21 research
  packet received a seven-page document-render fallback inspection.

These checks establish deterministic content identity, redaction and
fail-closed authority. They do not execute regression on a frozen build,
complete independent security review, validate Fidelity compatibility or
constitute founder UAT.

## Dependencies and forecast

- Issue #2: no authorized representative Fidelity export; compatibility is
  unverified.
- Issue #3: the inherited environment file still requires private owner review;
  its contents remain uninspected and unpublished.
- Issue #4: completed data-rights evidence and licensed datasets remain absent.
- Managed authentication, authorized private storage, restore evidence,
  verified log redaction and founder UAT remain 0/5.
- The defect register is open but formal calculation/privacy review and
  independent review are incomplete.

The November 28 stabilization boundary is 5 days away; the December 12 target
is 19 days away. The reduced local synthetic candidate remains feasible. A
fully authenticated private-account prototype is not currently forecast as
acceptable without the missing external controls and evidence. Protecting the
final two weeks requires no new feature scope after November 28.

## Three recommended decisions

1. **Freeze only the exact reduced local/synthetic candidate** on November 28
   if its manifest replay passes and no critical calculation or privacy defect
   remains open.
2. **Keep authenticated/private capability deferred** until all five M4
   controls and the Fidelity/data-rights prerequisites have actual evidence.
3. **Treat December 12 as a conditional acceptance gate, not automatic
   completion**; if G1 prerequisites remain blocked, deliver the local
   synthetic handoff plus an explicit gap and maintenance report.

All three entries are recommendations, not approvals. Record only the
founder's actual response against the exact published packet.

## Engineering concept

A **content-addressed build** is identified by what its files contain, not by a
moving label such as “latest.” Any byte change produces a different digest, so
test results can be tied to one exact candidate. The digest proves identity,
not correctness: defects, independent review and UAT remain separate evidence.
