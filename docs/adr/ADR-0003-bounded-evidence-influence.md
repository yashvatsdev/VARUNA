# ADR-0003 — Bounded Evidence Influence (and why it is not PPO clipping)

**Status:** Accepted · **Date:** 24 Aug 2026

## Context

Suspicious input data must not be able to dominate a downstream inference. Two obvious
approaches both fail:

- **Clip or correct the value.** Destroys real signal. A genuinely unusual current, a real
  high-speed transit, or a legitimately large slick is exactly the observation that
  matters — and clipping silently rewrites evidence, which is disqualifying for a system
  whose output is meant to be evidentiary.
- **Drop the record.** Loses the evidence entirely and biases the sample toward the
  ordinary. It also destroys the audit trail: PRAMAN cannot preserve what was discarded at
  ingestion.

A naming hazard also had to be settled. The mechanism resembles PPO's ratio clipping in
shape, and an early framing described it that way. That framing is wrong and actively
harmful: PPO clipping bounds a *policy update* during *training* of an RL agent. There is
no policy, no update, and no RL anywhere in VARUNA's core. Describing it as PPO would
invite an entirely reasonable question — "why is there reinforcement learning in your
evidence pipeline?" — with no good answer, and would misdescribe the mechanism to anyone
reading the code later.

## Decision

Each observation carries `influence_weight ∈ [0, 1]` in its `EvidenceEnvelope`, capped by
the source's trust state:

```
TRUSTED     → 1.0
DEGRADED    → 0.6
CONFLICTED  → 0.3
QUARANTINED → 0.0
```

Downstream inference multiplies each observation's contribution by its `influence_weight`.
**The value itself is never modified.** Quarantined data is retained in full as raw
evidence and contributes zero.

The mechanism is named **Bounded Evidence Influence**. The term "clipping" and any
reference to PPO are not to be used for it, in code, comments, docs, or presentations.

## Consequences

**Positive**
- Legitimate extreme observations survive intact.
- A compromised source is contained without erasing what it reported.
- Raw evidence is preserved, so PRAMAN's chain of custody holds.
- The cap is enforced by a Pydantic validator — an envelope that exceeds its trust ceiling
  cannot be constructed at all.

**Negative**
- Every consumer must actually apply the weight; a module that ignores it silently defeats the mechanism.
- The four ceiling values are judgement calls, not derived from data.

**Mitigation**
- Consumers that ignore `influence_weight` should be caught in review; NYAYA's use of it is
  contract-tested.
- Ceilings are configuration, and should be revisited once the rebuilt evaluation harness
  can measure their effect.

## Rejected alternatives

1. **Value clipping** — destroys real signal and rewrites evidence.
2. **Record dropping** — loses evidence and biases the sample.
3. **Boolean trusted/untrusted** — no gradation; a slightly stale field is not a spoofed one.
4. **Calling it PPO clipping** — factually wrong, invites a damaging question, misleads future readers.
