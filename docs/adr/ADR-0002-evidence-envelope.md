# ADR-0002 — Universal Evidence Envelope on every subsystem output

**Status:** Accepted · **Date:** 24 Aug 2026 · **Supersedes:** v1 loose metadata

## Context

In v1, quality was a single scalar `confidence` attached to a few payloads. Three failures
followed directly from that:

1. A trusted source producing a noisy measurement was indistinguishable from a spoofed
   source producing a clean one — both were "0.8 confidence".
2. Nothing carried provenance, so an artifact could not be traced to the raw bytes it came
   from. PRAMAN's evidentiary claim was not actually supportable.
3. Degradation did not propagate. A module consuming a fallback-climatology forcing field
   emitted output indistinguishable from one consuming live data, so the officer never saw
   that the origin field was unreliable.

## Decision

Every major subsystem output carries an `EvidenceEnvelope` (`varuna_contracts/evidence.py`)
with provenance, trust, influence weight, quality, uncertainty, calibration state, validity
state, degradation state, anomaly flags, and a content hash.

Downstream envelopes are constructed with `EvidenceEnvelope.derive()`, which enforces
**monotonic degradation**: the result is never more trusted, more valid, or less degraded
than the worst input.

Trust and confidence are separate fields with separate vocabularies:
- `trust: TrustState` — about the **source** (Data Guard's verdict)
- `quality.model_confidence` — about the **measurement** (the model's own estimate)

## Consequences

**Positive**
- Uncertainty propagation is structural, not a convention someone must remember.
- Provenance is always present, so PRAMAN's chain of custody is real.
- The validity gate has something concrete to evaluate.
- Property-based tests can assert the invariant across all state combinations (they do —
  `tests/contract/test_evidence_envelope.py`).

**Negative**
- Every module boundary gains boilerplate.
- Payload size grows (irrelevant at our volumes).
- Developers must remember to use `derive()` rather than constructing envelopes by hand.

**Mitigation**
- `derive()` is the documented path in the LLM guide and every ROLE file.
- Hand-construction that upgrades trust is a review-blocking defect.
- CI contract tests fail if the invariant is violated.

## Rejected alternatives

1. **Scalar confidence (v1)** — caused the three failures above.
2. **Envelope only at the API boundary** — internal propagation is exactly where degradation gets lost.
3. **Sidecar metadata table** — separable from the payload, so it drifts out of sync.
4. **Optional envelope** — optional invariants are not invariants.
