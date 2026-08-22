# P1 — ARCHITECT / Lead
## Owns: NYAYA (M7–M10) · evaluation harness · go/no-go rebuild · integration

You are the technical anchor. Two jobs: prove the mechanism actually works, then build the
inference that depends on it. Read `CLAUDE.md` and `docs/DECISIONS.md` §1 before anything.

> **The go/no-go has not been passed.** The existing harness cannot fail — see
> `docs/DECISIONS.md` §1. Rebuilt fairly, top-1 at 24 h / 20 vessels falls from 100% to
> ~12%. Days 1–2 are yours to establish the real number. Nobody quotes 100% anywhere.

---

## Day-by-Day

### Day 1 — unblock everyone, then fix the harness
- `src/eval/mock_phi.py` — generate a synthetic `.npz` in the exact `PhiFieldMeta` format
  (Gaussian blob drifting across time bins). **Ship this before lunch.** P5's entire week
  is blocked without it; P4 needs it to test serialisation.
- `experiments/go_nogo/core.py` — fix the traffic generator:
  - Add `hard_negative_fraction: float` and `hard_negative_miss_km: tuple[float,float]`.
    A hard negative transits within that miss distance of the true origin at a time offset
    sampled from ±8 h. Actually enforce `min_distance_deg` on the easy negatives.
  - Give every vessel (guilty included) a track spanning the full envelope, from before
    release to after observation. Add AIS gaps as a separate deliberate treatment.

### Day 2 — honest baseline + real L₀
- `src/eval/baselines.py` — three comparators:
  1. `nearest_vessel` — nearest to slick centroid at observation time.
  2. `cerulean_geometric` — **the one that matters.** Parity (slick major axis vs track
     bearing), proximity (slick head to nearest track point), temporality (AIS timestamp
     vs image capture), over an 8 h-before / 6 h-after window. Apache-2.0, documented at
     skytruth.org/cerulean/methods. Reimplement it properly — a straw-man baseline
     destroys the evidence slide.
  3. `single_backtrack` — one deterministic trajectory, Seatrack-style.
- Fix L₀ in the harness: total Φ mass minus mass inside the swept corridor of every
  observed track. Not a constant. Then run the test that was specified and never executed:
  delete the guilty track, measure detection rate; and with the guilty present, measure
  the false-latent rate.

### Day 3 — make the physics honest, then sweep
- Structural forcing bias: systematic speed (±15%) and direction (±12°) offset between the
  forward truth field and the backward model field, *on top of* the symmetric ensemble
  spread. Sweep bias magnitude as its own axis.
- Spatial structure: uniform flow + linear shear + one or two analytic eddies. Still fast,
  still no OpenDrift dependency, but the inverse problem is now ill-posed the way the real
  one is.
- Stop passing the true age in. Sample the backward window from a log-normal age prior.
- Vectorise the path integral (`np.digitize` + fancy index) before the sweep — the
  point-by-point KDE loop will not survive 3,000 trials.
- Launch the full sweep: age × density × forcing bias × hard-negative fraction, 50 trials
  per cell. Run it overnight.

### Day 4 — decision + NYAYA core
- One-page memo: the curve, the honest number, the call. Gates in `docs/DECISIONS.md`.
- `src/nyaya/path_integral.py` — `score_track(track, phi_array, meta) -> float` plus
  `closest_approach_km` and `phi_mass_explained` for the UI.
- `src/nyaya/latent.py` — corridor subtraction → `LatentSourceScore`, including the
  inferred release point and pseudo-track when L₀ dominates.

### Day 5 — priors, posterior, verdict
- `src/nyaya/emission_prior.py` — `gap_score`, `speed_anomaly`, `loiter_score`,
  `night_proximity`, `type_weight`. Hand-tuned weights, **published in the UI**. A defence
  lawyer can attack a black box; they cannot attack six disclosed numbers.
- `src/nyaya/posterior.py` — normalise `{L₀, π₁L₁ … π_kL_k}`, compute entropy, emit
  `VerdictType`. Flat posterior → `INCONCLUSIVE`, never a forced name.
- `src/nyaya/pipeline.py` — `attribute(detection, phi_meta, tracks) -> AttributionResult`.

### Day 6 — calibration + evidence
- `src/nyaya/calibration.py` — isotonic regression fit on the sweep's simulated truth;
  report ECE and a reliability diagram. **This is the strongest slide in the deck** and no
  competing team will have it. Protect it even if features get cut.
- `src/eval/ablations.py` — ensemble vs single trajectory · path integral vs nearest point
  · ± emission prior · ± latent term · ± wind channel.

### Day 7 — integration + Q&A
- Wire NETRA → PRATIVARTAN → NYAYA → PRAVAAH end to end on the hero case with P3 and P4.
- Build the deliberately inconclusive case (weak currents, dense traffic) for Moment 6.
- Q&A prep: the four questions in `docs/DECISIONS.md` and the honesty rules in `CLAUDE.md`.

---

## Files You Create

| Path | Purpose |
|---|---|
| `src/eval/mock_phi.py` | Synthetic Φ `.npz` — **day 1, unblocks P4 and P5** |
| `src/eval/baselines.py` | nearest-vessel · Cerulean geometric · single backtrack |
| `src/eval/harness.py` | Simulated case generator: release → drift → slick → traffic |
| `src/eval/sweep.py` | Parameter sweep + Monte Carlo driver |
| `src/eval/ablations.py` | Ablation table |
| `src/eval/metrics.py` | Top-1/top-3, ECE, reliability diagram, latent P/R |
| `src/nyaya/path_integral.py` | M7 — `L_k = Σ Φ(x_k(t), y_k(t), t) · Δt` |
| `src/nyaya/emission_prior.py` | M8 — behavioural π_k |
| `src/nyaya/latent.py` | M9 — residual-mass L₀ + inferred dark track |
| `src/nyaya/posterior.py` | M10 — normalisation, entropy, verdict |
| `src/nyaya/calibration.py` | M10 — isotonic fit, ECE |
| `src/nyaya/pipeline.py` | Entry point over `schemas.py` types |

## Interfaces

- **PRODUCE:** `AttributionResult`, `LatentSourceScore`, `VesselScore`, and the mock Φ
  `.npz` that P4/P5 develop against.
- **CONSUME:** `SlickDetection` (P2), `PhiFieldMeta` + `.npz` (P3), `list[VesselTrack]` (P4),
  `list[DarkVesselDetection]` (P2).
- **NEED FROM:** P3 by day 4 — a real Φ `.npz` matching the spec. P4 by day 4 — real
  `VesselTrack` objects from MarineCadastre. P2 by day 5 — a real `SlickDetection`.

## The path integral, precisely

```
L_k = Σ_i  Φ[t_i, y_i, x_i] · Δt_i

  x_i = digitize(track.lon(t_i), lon_edges) - 1
  y_i = digitize(track.lat(t_i), lat_edges) - 1
  t_i = digitize(unix(t_i),      time_edges) - 1

Drop samples outside the grid. Resample the track to the Φ time resolution first.
Then L_k *= emission_prior.combined.

L_0 = 1 - Σ_bins Φ[b] for every bin b inside ANY track's corridor
      (corridor = cells within NYAYA_CORRIDOR_KM of a track segment, at that time bin).

posterior = normalise({L_0, L_1 ... L_k})
entropy   = -Σ p log p / log(n)         # normalised to [0,1]
verdict   = INCONCLUSIVE            if entropy > NYAYA_INCONCLUSIVE_ENTROPY
            LATENT_SOURCE_DOMINANT  if argmax is L_0
            VESSEL_ATTRIBUTED       if top1 >= NYAYA_MIN_POSTERIOR_FOR_NAME
            else INCONCLUSIVE
```

## Claude Code Prompt

```
Read CLAUDE.md and tasks/P1_ARCHITECT.md. You are P1, the architect. You own NYAYA
(M7-M10), the evaluation harness, and the go/no-go rebuild.

Context that overrides any other note: the existing go/no-go in experiments/go_nogo/
is invalid — see docs/DECISIONS.md section 1. My first job is to rebuild it so it can
actually fail.

Import all shared types from src.common.schemas. Do not redefine them. Python 3.10+,
type hints, no tutorial comments.

Start with src/eval/mock_phi.py now — a synthetic Phi .npz in the exact PhiFieldMeta
format (keys: phi float32 (n_t,n_y,n_x) summing to 1, lon_edges, lat_edges, time_edges
unix seconds, particle_count int32). A Gaussian blob whose centre drifts across time
bins and whose width grows backward in time. P4 and P5 are blocked until it exists.
Write the file, then move to the traffic-generator fix in experiments/go_nogo/core.py.
```

## If Claude Is Offline

- Path integral: resample track to Φ time bins, `np.digitize` each axis, fancy-index,
  multiply by `Δt`, sum. Guard the out-of-grid indices.
- Corridor mask: for each time bin, rasterise track segments into the Φ grid with a
  `NYAYA_CORRIDOR_KM` buffer (`scipy.ndimage.binary_dilation` on a line mask is enough).
- Isotonic calibration: `sklearn.isotonic.IsotonicRegression(out_of_bounds="clip")`,
  fit `predicted_posterior → was_correct` over sweep trials.
- ECE: bin predictions into 10 bins, `Σ (n_b/N)·|acc_b − conf_b|`.
- Cerulean method reference: https://skytruth.org/cerulean/methods (parity, proximity,
  temporality; 8 h before / 6 h after).
