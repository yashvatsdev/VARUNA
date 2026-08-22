# VARUNA GRID — Architecture Decisions

Reasoning behind the bootstrap. `CLAUDE.md` is the summary; this is the why.

---

## 1. Go/no-go status: not established (overrides the bootstrap brief)

The bootstrap brief stated *"Result: GO — 100% top-1 at 24h/20 vessels. The core mechanism
is validated."* That was not written into `CLAUDE.md`, because the harness that produced
it cannot fail. Verified against `experiments/go_nogo/core.py`:

| Defect | Evidence |
|---|---|
| Innocent vessels are not competitors | Guilty passes 1.2 km from the true origin at the right time; nearest of 19 innocents is 32.8 km (median). Only 6.7% of trials have any innocent within 5 km. `min_distance_deg` is accepted and never used. |
| Baseline cannot win | `generate_guilty_track` spans release ±6 h; observation is at +24 h. The guilty vessel stopped broadcasting 18 h before the image in 100% of trials. |
| L₀ is a constant | `total_phi_mass` sums path integrals, not Φ mass, so `P(latent) = 1/(2N+1)` exactly — 0.0909 at N=5, 0.0244 at N=20, matching every CSV row. Zero information. |
| Physics is trivially invertible | Current field is spatially uniform (`velocity_at` ignores position) — no shear, no eddies. Backward ensemble is handed the *same* field object as forward, perturbed symmetrically about truth. |
| Leaks | `backward_duration = slick_age × 1.3` hands the system the true age. OpenDrift is not installed. `results/full_sweep/` is empty. |

Re-run at 24 h / 20 vessels, relaxing one assumption at a time (25 trials each):
as-is 80% → fair baseline 68% → hard negatives 24% → structural forcing bias **12%**.
Chance is 5%. There is signal; there is not yet a system.

**Consequence for the build:** the bootstrap proceeds anyway, because 6 of 8 subsystems are
identical under either outcome (Section 6 fallback in the roadmap). Only NYAYA's headline
claim is contingent. P1 rebuilds the harness first; nobody quotes 100% in any round.

---

## 2. Seven-day scope: what is CORE, IMPORTANT, CUT

Driven by Section 16.5 cut order and the six demo moments — a subsystem earns CORE status
only if a demo moment dies without it.

| Tier | Subsystems | Rationale |
|---|---|---|
| **CORE** | NETRA · PRATIVARTAN · NYAYA · CHHAYA · console (M14) | Moments 1, 2, 3, 6. Section 16.5 lists these as NEVER cut. |
| **IMPORTANT** | PRAVAAH · SMRITI (static) · PRAMAN | Moments 4, 5. Cheap: PRAVAAH is one extra OpenDrift call with a positive timestep; SMRITI ships as a pre-computed layer. |
| **REDUCED** | ABHIYAN | Greedy nearest-asset over Φ mass, not an LP. Still demonstrates "the system decides". |
| **MOCKED** | SETU | UI panel only. No SMS gateway. |
| **CUT** | PRAHARI live scheduler | Pre-ingest scenes; describe the standing watch on a slide. Zero demo value for real cost. |
| **CUT** | M15 LLM report drafting | Optional in the master context. Adds a failure mode to an evidence chain. |

Minimum set for all six moments: NETRA + PRATIVARTAN + NYAYA + CHHAYA + PRAVAAH + console,
plus a Cerulean-style geometric baseline (Moment 1 is *the baseline failing* — without it
there is no contrast) and a deliberately inconclusive case (Moment 6).

---

## 3. Integration: in-process calls, REST only at the edge

The pipeline is linear and auditable — `detect → backtrack → score → forecast`. No
branching, so no planner, no message bus between subsystems. Each subsystem is a Python
package exposing one entry function over `schemas.py` types. Celery exists only because
Φ takes minutes and HTTP must not block; the queue carries *jobs*, not inter-module
messages. A microservice mesh here would be theatre for six people.

Frontend talks REST + one WebSocket for progress. That is the only network boundary.

---

## 4. Φ format: 3-D histogram, not KDE

The go/no-go used `scipy.gaussian_kde` per time bin. It was the dominant cost, evaluated
point-by-point in a Python loop, and each bin normalised independently to 1 — so a tightly
converged bin and a diffuse one contributed equally, and a loitering vessel scored higher
purely by accumulating `dt`.

Replaced by a single 3-D histogram normalised **once** over the whole field:

```
phi            float32 (n_t, n_y, n_x)   sum(phi) == 1.0
lon_edges      float64 (n_x + 1,)
lat_edges      float64 (n_y + 1,)
time_edges     float64 (n_t + 1,)        unix seconds, UTC
particle_count int32   (n_t,)
```

Path-integral scoring becomes three `np.digitize` calls and a fancy-index — vectorised,
exact, no bandwidth parameter to defend in Q&A. It serialises directly to deck.gl's
`HeatmapLayer`, and the same array supports the corridor subtraction that L₀ needs.
Weight each time bin by the age prior before normalising, so temporal evidence is real.

`PhiFieldMeta.effective_area_km2` and `.spatial_entropy` are computed at build time and
drive the INCONCLUSIVE verdict downstream — the physics reports its own uncertainty
rather than NYAYA guessing at it.

---

## 5. Parallel tracks (zero cross-dependency until day 4)

| Track | Owner | Blocked by |
|---|---|---|
| Go/no-go rebuild + NYAYA + eval harness | P1 | nothing |
| NETRA training (GPU) + CHHAYA | P2 | dataset download only |
| OpenDrift engine + forcing cache | P3 | Copernicus account |
| API + AIS + PostGIS + SMRITI | P4 | nothing |
| Console on mock Φ | P5 | nothing — mock `.npz` generator ships day 1 |
| Demo cases, slides, video, rehearsal | P6 | nothing |

Only real convergence point is **day 4**, when P3's real Φ replaces P5's mock and P1's
scorer consumes it. Everything before that is independent. The mock Φ generator
(`src/eval/mock_phi.py`, P1 day 1) is what buys that independence — it is the single
highest-leverage half-hour in the week.

---

## 6. Hackathon hardening (Section 16.1: assemble, do not build)

- Every demo case ships with a pre-computed Φ `.npz` and a frozen `AttributionResult`
  JSON. `DEMO_MODE=true` serves those and skips compute entirely.
- All forcing cached as local NetCDF before travel. No live API call during a demo, ever.
- Console has a replay mode driven by a recorded WebSocket transcript.
- A 3-minute backup video recorded the day the pipeline first works — not the week before.
- Everything on a portable SSD, restored and tested on a second machine.

---

## 7. Deliberate omissions

No vector DB, no RAG, no agent framework, no Kubernetes, no model server. Section 11 rules
these out explicitly and the reasons hold: there is no corpus, no policy to learn, and
non-determinism in an evidence chain is a liability. The one retrieval need — recidivism
lookup — is a PostGIS `ST_DWithin`.
