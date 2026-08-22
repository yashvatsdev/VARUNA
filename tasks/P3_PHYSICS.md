# P3 — PHYSICS
## Owns: PRATIVARTAN (M5) · PRAVAAH (M11) · forcing data (M4)

You own the mechanism that makes VARUNA different from every other team: the backward
ensemble that turns a slick into an origin probability field. Read `CLAUDE.md` and the Φ
format in `docs/DECISIONS.md` §4 before writing anything.

> **Use `OceanDrift`, not `OpenOil`, for backtracking.** OpenOil models weathering —
> evaporation, emulsification — which is physically irreversible. Running it backward
> produces nonsense. Backtracking needs advection only. Use `OpenOil` for the *forward*
> PRAVAAH run if you want weathering there.

---

## Day-by-Day

### Day 1 — accounts and engine
- Register: Copernicus Data Space, CMEMS, CDS (ERA5). CDS API keys can take 24 h — do this
  first thing, before writing code.
- `pip install opendrift` (fall back to
  `conda install -c opendrift -c conda-forge opendrift` if pip resolution fails — it often
  does). Run the docs' "back and forth" example and confirm a negative `time_step` actually
  reverses a trajectory. Do not proceed until you have seen that work.

### Day 2 — forcing
- `src/prativartan/forcing.py`:
  - `fetch_currents(bbox, t0, t1)` — CMEMS `GLOBAL_MULTIYEAR_PHY_001_030` (reanalysis, for
    historical cases) via the `copernicusmarine` client.
  - `fetch_wind(bbox, t0, t1)` — ERA5 10 m u/v via `cdsapi`.
  - **Cache to `data/forcing/` as NetCDF, keyed by bbox+time hash.** Never hit a live API
    during a demo — Section 16.1. Every fetch writes a `.json` sidecar recording product
    ID and version; PRAMAN needs it.
- Pull three regions × one month: Arabian Sea / Mumbai High, Bay of Bengal / Chennai, and
  Gulf of Mexico (the last is where P4's real AIS lives, so it is our validation region).

### Day 3 — the backward ensemble
- `src/prativartan/ensemble.py`:
  - Seed `PHI_N_PARTICLES` across the slick mask (not at its centroid — across the mask).
  - `PHI_N_ENSEMBLE` members, each perturbing: wind-drift factor ∈ [0.02, 0.04],
    horizontal diffusivity ∈ [5, 50] m²/s, and a current-field realisation.
  - **Ensemble members must differ structurally, not just by jitter.** Perturbing one
    field around its own mean keeps the ensemble centred on a possibly-wrong answer. Draw
    members from *different products* where you can — CMEMS analysis, CMEMS reanalysis,
    and a shifted/scaled variant — so the spread reflects genuine model disagreement.
    P1's sweep shows structural bias is the dominant error source.
  - Backward duration from the **age prior distribution** on `SlickDetection`, sampled per
    member — not a single true age. `duration = PHI_BACKWARD_MARGIN × prior upper bound`.
  - Negative `time_step`. `OceanDrift`, not `OpenOil`.

### Day 4 — build Φ and hand it over
- `src/prativartan/phi.py` — accumulate all member trajectories into **one 3-D histogram**,
  normalised once over the whole field. Exact `.npz` spec in `docs/DECISIONS.md` §4.
  Weight each time bin by the age prior before normalising, so temporal evidence is real
  rather than an artefact of bin occupancy.
- Compute `effective_area_km2` (smallest area containing 90% of mass) and
  `spatial_entropy` into `PhiFieldMeta` — these drive P1's INCONCLUSIVE verdict. The
  physics reports its own uncertainty; NYAYA should not have to guess it.
- **Deliver a real Φ `.npz` to P1 and P5 today.** They have been on P1's mock since day 1.

### Day 5 — PRAVAAH
- `src/pravaah/forecast.py` — same engine, positive timestep, 24–72 h horizon. `OpenOil`
  is appropriate here if you want weathering.
- `src/pravaah/landfall.py` — intersect forward particles with a GSHHG coastline, geocode
  the strike to a **named** beach, compute ETA and probability per segment. "Oil reaches
  Marina Beach in 31 h 20 m" is Demo Moment 4 and it needs a real place name.

### Day 6 — performance
- Φ must compute in **under 2 minutes** on demo hardware. Multiprocess across ensemble
  members (embarrassingly parallel). If you blow the budget, reduce M and *report the
  widened uncertainty* — never silently truncate the ensemble.
- Pre-compute and freeze Φ for every demo case into `data/cache/`.

### Day 7 — integration
- Wire NETRA → PRATIVARTAN → NYAYA with P1 and P2 on the hero case. Build the weak-current
  case for Moment 6 — Φ stays diffuse and the system says so.

---

## Files You Create

| Path | Purpose |
|---|---|
| `src/prativartan/forcing.py` | M4 — CMEMS + ERA5 fetch, cache, version sidecars |
| `src/prativartan/readers.py` | OpenDrift reader construction from cached NetCDF |
| `src/prativartan/ensemble.py` | M5 — backward ensemble, perturbed forcing |
| `src/prativartan/phi.py` | Φ 3-D histogram builder + `PhiFieldMeta` |
| `src/prativartan/pipeline.py` | `backtrack(detection) -> PhiFieldMeta` |
| `src/pravaah/forecast.py` | M11 — forward drift |
| `src/pravaah/landfall.py` | Coastline intersection + named landfall |
| `scripts/cache_forcing.py` | Bulk pre-download for all demo regions |

## The Φ contract — do not deviate

```
data/cache/phi_<phi_id>.npz
  phi            float32 (n_t, n_y, n_x)   sum(phi) == 1.0   (t ascending)
  lon_edges      float64 (n_x + 1,)
  lat_edges      float64 (n_y + 1,)
  time_edges     float64 (n_t + 1,)        unix seconds UTC
  particle_count int32   (n_t,)
```

P1 indexes it with `np.digitize`; P5 renders it as a `HeatmapLayer`. If the shapes or the
normalisation drift from this, both break silently. Assert `abs(phi.sum() - 1) < 1e-6`
before writing.

## Interfaces

- **PRODUCE:** `PhiFieldMeta` + the `.npz` (→ P1, P5), `ForwardForecast` +
  `LandfallPrediction` (→ P4, P5), cached ERA5 wind grids (→ P2).
- **CONSUME:** `SlickDetection` (P2) — mask path and the age prior.
- **NEED FROM:** P2 by day 4 — a real `SlickDetection` with a mask. P6 by day 2 — the demo
  regions and dates so caching can start early.

## Claude Code Prompt

```
Read CLAUDE.md, tasks/P3_PHYSICS.md, and docs/DECISIONS.md section 4. You are P3,
physics. You own PRATIVARTAN (backward ensemble -> Phi field), PRAVAAH (forward drift
-> landfall), and forcing data.

Two hard rules: use OceanDrift not OpenOil for backtracking (weathering is
irreversible), and Phi is a 3-D histogram normalised once over the whole field, not a
per-time-bin KDE.

Import shared types from src.common.schemas — PhiFieldMeta, SlickDetection,
ForwardForecast. Do not redefine them. Python 3.10+, type hints.

Start with src/prativartan/forcing.py now — CMEMS current and ERA5 wind fetchers that
cache to data/forcing/ as NetCDF keyed by a bbox+time hash, each with a JSON sidecar
recording product ID and version. Never call a live API twice for the same request.
```

## If Claude Is Offline

- OpenDrift docs: https://opendrift.github.io — see the "back and forth" example.
- Backward run: `o.run(duration=timedelta(hours=H), time_step=-900)`. Negative step is all
  that reverses it.
- Config keys: `drift:wind_drift_factor`, `drift:horizontal_diffusivity`,
  `environment:fallback:x_sea_water_velocity` (and `y_`, `x_wind`, `y_wind`).
- CMEMS: `copernicusmarine.subset(dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m", ...)`,
  variables `uo`, `vo` at the surface depth level.
- ERA5: `cdsapi.Client().retrieve("reanalysis-era5-single-levels", {...})`,
  variables `10m_u_component_of_wind`, `10m_v_component_of_wind`.
- Histogram: `np.histogramdd(np.column_stack([t, lat, lon]), bins=[t_edges, lat_edges,
  lon_edges])`, then divide by the total.
- Coastline: GSHHG shapefile via GeoPandas; `shapely.STRtree` for fast intersection.
