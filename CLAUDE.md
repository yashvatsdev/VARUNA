# VARUNA GRID

Oil spill detection + probabilistic vessel attribution for SIH 2026 (PS SIH26143, NTRO).
Ensemble reverse advection → origin field Φ(x,y,t) → path-integral scoring of AIS tracks
→ calibrated posterior including a latent dark-vessel hypothesis.

Source of truth for domain/strategy: `VARUNA_MASTER_CONTEXT.md`. Architecture reasoning:
`docs/DECISIONS.md`. Per-person work: `tasks/P*.md`.

## Status (23 Aug 2026)

- **Go/no-go: NOT YET ESTABLISHED.** `experiments/go_nogo/` returned 100% top-1 at
  24h/20v, but that harness cannot fail: innocent vessels are drawn a median 33 km from
  the origin, the guilty track ends 18 h before the observation so the baseline can never
  win, L₀ is a constant `1/(2N+1)`, and the backward ensemble is centred on the exact
  truth field. Rebuilt fairly, top-1 falls to ~12%. See `docs/DECISIONS.md` §1.
  **P1 rebuilds and re-runs the sweep before NYAYA is trusted.** Do not quote 100%.
- Bootstrap complete: schemas, config, skeleton, task files. No subsystem code yet.

## Architecture

```
PRAHARI(cut) → NETRA → PRATIVARTAN → NYAYA ←── CHHAYA
                 M2,M3      M5          M7-M10     xView3
                              ↓           ↓
                          PRAVAAH      ABHIYAN → PRAMAN → SMRITI
                            M11        greedy     M13      M12
```
Linear, auditable, no branching. In-process Python calls; REST only for the frontend.

## Stack (Section 14 — locked)

OpenDrift · PyTorch + segmentation-models-pytorch · rasterio/xarray/GeoPandas/Shapely ·
FastAPI + Celery + Redis · PostgreSQL+PostGIS · MinIO · React + MapLibre GL + deck.gl ·
TorchScript · Docker Compose.

## Layout

```
src/common/schemas.py   THE contract. Every subsystem imports from here. Change = tell all.
src/common/{config,geo_utils,logging}.py
src/{netra,prativartan,nyaya,chhaya,pravaah,ais,smriti,abhiyan,praman}/
src/api/routes/         FastAPI
src/eval/               simulation harness, sweeps, calibration, ablations
tasks/P1..P6            self-contained per-person plans
experiments/go_nogo/    week-1 discriminability harness (being rebuilt)
```

## Key interfaces

- `SlickDetection` — NETRA → PRATIVARTAN. Carries an age **distribution**, not a point.
- `PhiFieldMeta` + `.npz` — PRATIVARTAN → NYAYA/frontend. 3-D histogram, not KDE.
  Keys: `phi(n_t,n_y,n_x) float32 sum=1`, `lon_edges`, `lat_edges`, `time_edges(unix)`,
  `particle_count`.
- `VesselTrack` — AIS → NYAYA. `transponder_active=False` drives the judge control.
- `AttributionResult` — NYAYA → everything. Posteriors sum to 1 **with** `latent_source`.

## Conventions

Python 3.10+, full type hints, Pydantic v2, structlog. UTC tz-aware datetimes only.
WGS84 (lon, lat) ordering. km / km² / knots. Absolute imports from `src.`.
Model + forcing versions recorded on every artefact — PRAMAN depends on it.

## Honesty rules (Section 18, abbreviated)

Attribution is **not** unsolved (Cerulean, CleanSeaNet ship it). Backward drift is **not**
our innovation (the PS asks for it; Seatrack has done it 20 years). Ours is the
probabilistic formulation: ensemble uncertainty, path integral, latent term, calibration.
Simulated evaluation ≠ operational validation. Indian AIS is synthetic — say so on the
slide. Never "patentable", never "real-time", never "no Indian system exists". The system
never names a ship without human sign-off. INCONCLUSIVE is a valid output.

## Working with this repo (for future LLM sessions)

Read this file once at session start; do not re-read `VARUNA_MASTER_CONTEXT.md` unless
strategy is in question — cite it by section number instead. One subsystem per session.
Import shared types from `src.common.schemas`; never redefine them. Write code directly,
no design essays. Prefer editing over rewriting. Keep this file under 100 lines.
