# ROLE 01 — Scientific / ML Lead

**Owns:** NETRA · PRATIVARTAN · NYAYA · CHHAYA · calibration · uncertainty · scientific evaluation

You own the claim. Everything the team says about accuracy, calibration, and honesty
traces back to code you wrote. Read `LLM_IMPLEMENTATION_GUIDE.md` §10 for your module
contracts and `FAILURE_THREAT_MATRIX.md` §3–4 for the failures you must contain.

---

## 0. Read this first — the harness is invalid

`experiments/go_nogo/` reports 100% top-1 at 24 h / 20 vessels. **That number cannot be
used.** Verified defects (`docs/DECISIONS.md` §1):

| Defect | Evidence |
|---|---|
| Innocent vessels are not competitors | Guilty passes 1.2 km from the true origin; nearest innocent 32.8 km (median). `min_distance_deg` accepted and never used. |
| Baseline structurally cannot win | Guilty track spans release ±6 h; observation at +24 h. Guilty stopped broadcasting 18 h before the image in 100% of trials. |
| L₀ is a constant | `total_phi_mass` sums path integrals, not Φ mass → `P(latent) = 1/(2N+1)` exactly. Zero information. |
| Inverse problem is trivial | Current field spatially uniform; backward ensemble handed the same field object as forward, perturbed symmetrically about truth. |
| Leaks | `backward_duration = slick_age × 1.3` passes the true age. |

Rebuilt fairly: 80% → 68% (fair baseline) → 24% (hard negatives) → **12%** (structural
forcing bias). Chance is 5%. There is signal; there is not yet a system.

**Days 1–2 are the rebuild. Nobody publishes a number until it passes the validity
checklist in `FAILURE_THREAT_MATRIX.md` §8.**

---

## Scientific assumptions you must defend

| Assumption | Status | If challenged |
|---|---|---|
| Backward advection recovers origin under known forcing | Holds for uniform fields; degrades sharply under structural bias | Show the sensitivity block |
| CMEMS 1/12° resolves the relevant flow | **Unproven at our scale** — ~8 km grid is a physical floor | State it; report `forcing_sensitivity` |
| Age can be inferred from morphology | Weak — PS says "if feasible" | Always a distribution; report `age_sensitivity` |
| Diffusivity range 5–50 m²/s | Literature-typical, not site-calibrated | Sweep it; report sensitivity |
| Simulated truth calibrates real posteriors | **Only given correct physics** | Honesty rule — never claim operational validation |

---

## Day-by-day

### Day 1 — unblock the team, then fix the generator
- `packages/varuna_nyaya/mock_phi.py` — synthetic `PhiField` + `.npz` in the locked
  format. **Ship before lunch.** ROLE 03 and ROLE 04 are blocked without it.
- `experiments/go_nogo/` — parameterise hard negatives: `hard_negative_fraction`,
  `miss_km` range, `time_offset_h` range. Enforce `min_distance_deg` on easy negatives.
- Every vessel broadcasts across the full envelope. AIS gaps become a separate treatment.

### Day 2 — honest baseline + real L₀
- `experiments/baselines/` — three comparators:
  1. `nearest_vessel` (naïve)
  2. `cerulean_geometric` — **the one that matters.** Parity, proximity, temporality over
     8 h-before/6 h-after. Apache-2.0, documented at skytruth.org/cerulean/methods.
  3. `single_backtrack` (Seatrack-style, deterministic)
- L₀ = total Φ mass − mass inside the swept corridor of every observed track. Then run
  the never-executed test: delete the guilty track → detection rate; guilty present →
  false-latent rate.

### Day 3 — honest physics, then sweep
- Structural forcing bias: systematic speed (±15%) and direction (±12°) offset between
  forward truth and backward model, **on top of** symmetric ensemble spread.
- Spatial structure: uniform + linear shear + 1–2 analytic eddies. No OpenDrift needed.
- Sample the backward window from a log-normal age prior — stop passing the true age.
- Vectorise the path integral (`np.digitize` + fancy index) before sweeping.
- Launch: age × density × forcing bias × hard-negative fraction, 50 trials/cell. Overnight.

### Day 4 — decision + NYAYA core
- One-page memo: the curve, the honest number, the call. Gates in `docs/DECISIONS.md`.
- `packages/varuna_nyaya/path_integral.py` — `L_k`, plus `closest_approach_km` and
  `phi_mass_explained` for the UI.
- `packages/varuna_nyaya/latent.py` — corridor subtraction → latent probability +
  `LatentFinding` + inferred point.

### Day 5 — priors, posterior, distinguishability, gate
- `packages/varuna_nyaya/priors.py` — the six published sub-scores (`PriorContribution`).
- `packages/varuna_nyaya/posterior.py` — normalise, entropy, `top_gap`,
  **`distinguishability` (separation, not peakedness)** → `DecisionState`.
- `packages/varuna_nyaya/validity_gate.py` — `ValidityGateResult`. This is the mandatory
  chokepoint before any operational consumer.

### Day 6 — NETRA + CHHAYA
- `packages/varuna_netra/` — U-Net ResNet34, 3 channels (VV, VH, ERA5 wind), 3 classes.
  See `ML_TRAINING_GUIDE.md`. Report look-alike FP rate **separately**.
- Age prior as a **log-normal distribution**, never a point.
- `packages/varuna_chhaya/` — xView3 wrapper. Distinguish all four `LatentFinding` values;
  `INSUFFICIENT_COVERAGE` when the footprint cannot support a conclusion.

### Day 7 — integration only
- Wire NETRA → PRATIVARTAN → NYAYA on CASE-0001 with ROLE 02/04. No new features.
- Build the deliberately inconclusive case (weak currents, dense traffic).
- Ablation table + reliability diagram for the evidence slide.

---

## Files you create

```
packages/varuna_nyaya/{path_integral,priors,latent,posterior,validity_gate,calibration,mock_phi,pipeline}.py
packages/varuna_netra/{dataset,model,train,evaluate,characterise,inference,export}.py
packages/varuna_chhaya/{detector,match,finding}.py
packages/varuna_prativartan/{ensemble,phi,diagnostics,sensitivity,pipeline}.py   # with ROLE 04
experiments/{go_nogo,baselines,convergence,forcing_bias,multimodality}/
tests/scientific/test_{nyaya,phi,calibration}_*.py
```

## Interfaces

- **PRODUCE:** `SlickDetection`, `PhiField`, `AttributionResultV2`, `ValidityGateResult`, `DarkVesselDetection`, and the day-1 mock Φ.
- **CONSUME:** trusted forcing + AIS from ROLE 02 (day 4+), enveloped inputs only.
- **NEED:** ROLE 02 by day 4 — real `VesselTrack` from MarineCadastre + cached forcing.
  ROLE 04 by day 2 — OpenDrift installed and verified backward-capable.

## The maths, precisely

```
L_k = Σ_i Φ[t_i, y_i, x_i] · Δt_i        # digitize per axis, drop out-of-grid
L_k *= prior.combined * influence_weight
L_0 = 1 − Σ Φ[cells within corridor_km of ANY track segment at that time bin]
posterior = normalise({L_0, L_1..L_k})
top_gap = p(1) − p(2)
entropy = −Σ p log p / log(n)
distinguishability: separation between top candidates in Φ-space,
                    NOT posterior peakedness — two vessels in one lobe
                    can produce a sharp posterior and must still be
                    reported NOT_DISTINGUISHABLE
```

## Acceptance criteria

- [ ] Harness passes the §8 validity checklist
- [ ] `test_latent_not_constant.py` passes (L₀ varies with geometry)
- [ ] Posterior sums to 1 with latent (contract-enforced)
- [ ] ECE reported with a reliability diagram
- [ ] `NOT_DISTINGUISHABLE` fires on the two-vessels-one-lobe case
- [ ] Every Φ carries populated diagnostics + sensitivity
- [ ] Ablation table: ensemble vs single · path-integral vs nearest-point · ±prior · ±latent · ±wind channel

## Do NOT touch

`apps/api`, `apps/web`, Docker/CI, alerts, missions, PRAMAN internals. If you need a
contract change, write an ADR — do not edit `varuna_contracts` unilaterally.

## Claude Code prompt

```
Read LLM_IMPLEMENTATION_GUIDE.md and tasks/ROLE_01_SCIENTIFIC_ML.md. You are ROLE 01,
scientific/ML lead, owning NETRA, PRATIVARTAN, NYAYA, CHHAYA, calibration.

Overriding context: experiments/go_nogo/ is INVALID — see docs/DECISIONS.md section 1
and FAILURE_THREAT_MATRIX.md section 8. Its 100% result must never be quoted. Days 1-2
are the rebuild.

Import all types from varuna_contracts. Never redefine them. Build downstream envelopes
with EvidenceEnvelope.derive(). Python 3.12, full type hints, seeded randomness.

Start with packages/varuna_nyaya/mock_phi.py — a synthetic PhiField plus .npz in the
locked format (phi float32 (n_t,n_y,n_x) summing to 1, lon_edges, lat_edges, time_edges
unix, particle_count), with populated PhiDiagnostics and SensitivityBlock. ROLE 03 and
ROLE 04 are blocked until it exists.
```
