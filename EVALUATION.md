# EVALUATION.md
## VARUNA GRID v2 — evaluation protocol

---

## 0. The harness is currently invalid — read this first

`experiments/go_nogo/` reports **100% top-1 at 24 h / 20 vessels**. That number cannot be
used, published, or calibrated on.

**Verified defects** (measured against `experiments/go_nogo/core.py`):

| Defect | Evidence |
|---|---|
| Innocent vessels are not competitors | Guilty passes 1.2 km from the true origin at the right time; nearest of 19 innocents is 32.8 km (median). Only 6.7% of trials have any innocent within 5 km. `min_distance_deg` is a parameter that is accepted and never used. |
| Baseline structurally cannot win | Guilty track spans release ±6 h; observation is at +24 h. The guilty vessel stopped broadcasting 18 h before the image in **100%** of trials. |
| Latent term is a constant | `total_phi_mass` sums path integrals rather than Φ mass, so `P(latent) = 1/(2N+1)` exactly — 0.0909 at N=5, 0.0244 at N=20, matching every CSV row. Zero information. |
| Inverse problem is trivial | Current field is spatially uniform (`velocity_at` ignores position); the backward ensemble is handed the *same* field object as the forward run, perturbed symmetrically about truth. |
| Leaks | `backward_duration = slick_age × 1.3` passes the true age into the system. |

**Rebuilt fairly**, relaxing one assumption at a time (25 trials each, same seed):

| Condition added | Top-1 | Top-3 |
|---|---|---|
| As-is | 80% | 100% |
| + fair baseline (guilty keeps broadcasting) | 68% | 100% |
| + hard negatives (40% of traffic transits near origin) | 24% | 72% |
| + structural forcing bias | **12%** | 44% |

Chance at 20 vessels is 5% top-1, 15% top-3. **There is signal. There is not yet a system.**

---

## 1. Harness validity checklist

**No number leaves `experiments/` until every box is ticked** (threat E-01).

- [ ] Hard negatives are a swept parameter, with a controlled fraction transiting near the true origin
- [ ] Guilty and innocent vessels broadcast across the same time envelope
- [ ] Baseline is a faithful Cerulean reimplementation (parity/proximity/temporality, 8 h before / 6 h after), not a straw man
- [ ] L₀ varies with track geometry — asserted by `test_latent_not_constant.py`
- [ ] Forward truth field and backward model field differ **structurally**, not by symmetric jitter
- [ ] Current field has spatial structure (shear, eddies)
- [ ] True slick age is **not** passed in; age sampled from a prior
- [ ] Trial count gives a CI narrow enough for the claim being made
- [ ] Seeds recorded; run reproducible from the committed config

---

## 2. North-star KPI

> **Top-1 attribution accuracy at 24-hour slick age with ≥20 vessels in the envelope,
> subject to ECE < 0.05.**

One number. It fixes the operationally realistic case (a day-old slick in real traffic —
India's default), demands the baselines be beaten where they actually break, and the
calibration constraint prevents winning by confident guessing.

---

## 3. Revised decision gates

Measured at 24 h / 20 vessels / medium forcing bias / 30% hard negatives. These are lower
than the v1 gates because the task is now real.

| Top-1 | Top-3 | Call |
|---|---|---|
| ≥ 40% | ≥ 70% | **Strong go.** Full RDPA claim. |
| 25–40% | ≥ 60% | **Go**, but lead with top-3 + calibration rather than top-1. |
| 15–25% | 40–60% | **Conditional.** Emission priors + multi-product ensemble, then re-sweep. |
| < 15% | < 40% | **Reframe** as calibrated shortlist / origin-region narrowing. 6 of 8 subsystems survive. |

**If the rebuilt sweep lands in the 40–60% top-3 region, reframe the product as a
calibrated ranked shortlist rather than an attribution engine.** That is a search box a
Dornier can fly, it is honest, and it is still the strongest entry in this problem
statement.

---

## 4. Simulation protocol

```
real AIS track → simulated release at a known point and time
              → advect forward under REAL forcing (CMEMS + ERA5)
              → render a realistic slick
              → hand the system ONLY the slick and the surrounding traffic
```

Truth is known by construction; difficulty is a dial we control.

**Honesty constraint:** this measures whether the *inference* is sound **given the
physics**. It cannot measure whether the physics matches the real Bay of Bengal. Those are
different claims and must never be conflated.

---

## 5. Axes

| Axis | Values |
|---|---|
| Slick age | 2 / 6 / 12 / 24 / 48 h |
| Traffic density | 5 / 20 / 50 / 100+ vessels |
| Forcing error | low / medium / high, **including structural bias** |
| Hard-negative fraction | 0 / 15 / 30 / 45% |
| AIS quality | clean / gaps 20–120 min / spoofed |

Monte Carlo: ≥ 50 trials per cell; 100 where the CI matters for a published claim.

---

## 6. Baselines

1. **Nearest vessel** to the slick centroid at observation time — the naïve heuristic.
2. **Cerulean-style geometric** — parity, proximity, temporality over an 8 h-before /
   6 h-after window. Apache-2.0, publicly documented. **This is the comparison that
   matters**; a straw-man baseline invalidates the evidence slide.
3. **Single deterministic backtrack** — Seatrack-style, one trajectory, no ensemble.

All three plotted on the same accuracy-vs-age axes as VARUNA.

---

## 7. Metrics

| Metric | Definition |
|---|---|
| Top-1 / Top-3 | Guilty vessel ranked first / in the top three |
| **ECE** | 10 bins, `Σ (n_b/N)·|acc_b − conf_b|`. Target < 0.05 |
| Reliability diagram | Predicted vs observed frequency. **The strongest slide in the deck** |
| `distinguishability` | Separation between top candidates — **not** posterior peakedness |
| Latent P/R | Delete the guilty track → detection rate; guilty present → false-latent rate |
| INCONCLUSIVE rate | Fraction refused — should rise with age and traffic density |
| Segmentation IoU / F1 | Zenodo test split |
| **Look-alike FP rate** | ESSD set, **reported separately** |
| Φ effective support | km² holding 90% of mass, vs age |
| Convergence failure rate | Fraction of cases where the ensemble does not converge |

---

## 8. Ablations

| Ablation | Question |
|---|---|
| Ensemble → single trajectory | Does ensemble uncertainty buy anything? |
| Path integral → nearest point | Does the integral beat proximity? |
| ± emission prior | How much is physics vs behaviour? |
| ± latent term | Does L₀ improve or distort the posterior? |
| ± wind channel (NETRA) | Expect the gain concentrated in low-wind look-alikes |
| ± structural ensemble diversity | Does multi-product beat parameter jitter? |
| N, M sweep | The compute/accuracy frontier |

---

## 9. Robustness

Each row in `FAILURE_THREAT_MATRIX.md` becomes a test. Specifically:

- Injected current-field error (magnitude and direction bias)
- AIS gaps 20–120 min; spoofed positions
- Degraded segmentation (dilated/eroded masks)
- Two overlapping slicks from different sources
- Weak-current regimes where Φ stays diffuse
- Forcing outage → climatology fallback
- Correlated source bias

**Publish the failures.** Slow-current cases where Φ stays diffuse, and dense shipping
lanes where many tracks cross the origin, earn more credibility than hiding them.

---

## 10. Reporting rules

- Every number carries its uncertainty and its trial count.
- Every claim states the conditions it holds under.
- Baselines appear on the same axes.
- Failure cases are shown, not omitted.
- Simulated evaluation is labelled as such **every time it appears**.
- No number is quoted that did not come from a run passing the §1 checklist.
