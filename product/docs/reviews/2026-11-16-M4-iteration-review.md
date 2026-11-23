# M4 asynchronous concept and iteration review — November 16, 2026

Prepared November 16, 2026 at 19:24 Asia/Manila.

**State: review packet prepared on date; M4 remains blocked and deferred.**
This packet is not a completed meeting, founder response, decision approval,
milestone acceptance, deployment approval or release.

## Demo

From `product/`:

```sh
python3 -m atlas --m4-iteration-review-demo
```

Expected result: exit 3 with `receipt_state=review_packet`, `status=blocked`,
`review_timing=prepared_on_date`, a bound late-checkpoint summary, 0/5 private
controls ready, five dependencies and exactly three recommendations. Every
authority flag remains false.

The useful product demonstration remains the fixed localhost synthetic flow:
two reconciled invented rows, the public research gate state, two fixed option
scenarios and four option controls. It is a reduced read-only workflow, not an
authenticated private application or Fidelity-compatible import.

## Planned versus shipped

| Planned by M4 | Actually shipped | Review state |
|---|---|---|
| Authenticated private read-only prototype | Localhost synthetic read-only checkpoint | Reduced scope only |
| Managed authentication, authorized storage, restore evidence, redacted logs and founder UAT | Typed control register showing 0/5 evidenced | Blocked; all five deferred |
| November 14 dated weekly public-evidence update | No November 14 packet on the branch | Catch-up required with its actual date; do not backdate |

M3 engineering evidence is 6/6, but no M3 milestone acceptance is recorded.
The November 15 M4 execution is bound, late and blocked. No new founder
response exists on the live PR.

## QA

- Six direct iteration-review tests pass.
- Twelve direct checkpoint tests and all 38 CLI tests pass in the 56-test
  focused run.
- Full local suite: 488 tests passed in 17.537 seconds.
- Hosted verification: [GitHub Actions run 44071101138](https://github.com/lvlunario/quant_trading_tool/actions/runs/44071101138)
  passed on exact published review head `632915d`.

These checks prove typed composition, timing, exact recommendation count,
redaction and fail-closed authority. They do not implement or validate the five
missing private controls, Fidelity compatibility, licensed source access or
founder UAT.

## Dependencies and forecast

- Issue #2: no authorized representative Fidelity export; compatibility is
  unverified.
- Issue #3: the inherited environment file still requires private owner
  review; its contents remain uninspected and unpublished.
- Issue #4: completed data-rights evidence and licensed datasets are absent.
- Explicit M3 and M4 milestone dispositions remain unrecorded.
- The missed Saturday evidence packet needs a current, separately dated
  catch-up; CRBS remains blocked pending issuer/exchange/class evidence.

The November 28 stabilization boundary is 12 days away; the December 12 target
is 26 days away. A reduced local synthetic release candidate remains feasible.
An authenticated private prototype is at risk while all five private controls
remain unevidenced. Protecting the final two weeks requires freezing scope on
November 28 rather than consuming stabilization time with new features.

## Three recommended decisions

1. **Adopt the reduced local synthetic release candidate** as the achievable
   December fallback, while keeping its limitations visible.
2. **Defer the authenticated private milestone** until managed authentication,
   authorized storage, restore evidence, log-redaction verification and founder
   UAT actually exist.
3. **Freeze scope for stabilization on November 28** and allow only defect,
   evidence, security and acceptance work afterward.

All three entries are recommendations, not approvals. Record only a founder's
actual response against the exact published packet.

## Engineering concept

An **evidence plane** records what the system can prove; a **decision plane**
records what an authorized person accepts. Separating them prevents passing
tests or an elapsed date from silently becoming product acceptance. This
packet improves the evidence plane while deliberately leaving the decision
plane unchanged.
