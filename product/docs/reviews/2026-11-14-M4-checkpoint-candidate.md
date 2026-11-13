# M4 checkpoint candidate — November 14, 2026

Prepared November 13, 2026 at 19:20 Asia/Manila.

**State: candidate only.** This packet is not a completed review, meeting,
founder response, milestone acceptance, deployment approval or release.

## Demo

From `product/`:

```sh
python3 -m atlas --m4-checkpoint-demo
```

Expected result: exit 3 with `receipt_state=candidate`, `status=blocked`,
checkpoint date November 14, 0/5 private controls ready, five
`recommend_defer` rows and no acceptance or authority flags.

## Planned versus shipped

| M4 expectation | Evidence available | Checkpoint state |
|---|---|---|
| Integrated import → research → options workflow | Fixed localhost synthetic composition: 2 reconciled invented rows, research gates 8/8/0/0/0/0, 2 option scenarios, 4 controls | Available as synthetic fallback only |
| Managed authentication and access denial | Fifteen-minute exact-route localhost request boundary; no identity verification | Defer |
| Authorized private storage | No authorized private store provisioned | Defer |
| Recovery and restore demonstration | No restore evidence | Defer |
| Redacted operational logging | No independent redaction verification | Defer |
| Founder end-to-end UAT | No M4 UAT response recorded | Defer |

## QA

- Seven direct checkpoint tests pass.
- All 36 CLI tests pass.
- Full local suite: 475 tests passed in 13.115 seconds.
- Candidate-head hosted verification: Atlas foundation run #366 passed.

These results verify the checkpoint contract and existing synthetic fallback.
They do not implement or test the five missing private controls.

## Dependencies

- Issue #2: no authorized representative Fidelity export; compatibility
  remains unverified.
- Issue #3: inherited environment file still requires private owner review;
  contents remain uninspected and unpublished.
- Issue #4: completed data-rights evidence and licensed datasets remain absent.
- M3 engineering evidence is 6/6, but milestone acceptance remains unrecorded.

## Recommended disposition

**Defer M4 private-application acceptance. Continue only the local synthetic
fallback and bounded stabilization preparation.**

Rationale: engineering visibility cannot substitute for authentication,
authorized storage, recovery proof, verified log redaction or founder UAT.
Advancing the private milestone would misstate both security and acceptance.

## Founder decision requested

- Pending: approve the recommended M4 deferral/reduced synthetic fallback,
  request bounded changes, or provide another explicit disposition.

No response is recorded by preparing this packet.
