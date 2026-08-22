# P4 — BACKEND
## Owns: API (FastAPI) · AIS pipeline (M6) · PostGIS · SMRITI (08) · ABHIYAN (07, greedy)

You own the spine everyone else's output flows through, and the only real traffic
geometry we have — Gulf of Mexico AIS. Read `CLAUDE.md` first.

---

## Day-by-Day

### Day 1 — schema and skeleton
- `docker compose up postgres redis minio` from the repo root. Verify all three answer.
- `src/api/db.py` — SQLAlchemy engine + session, PostGIS extension enabled on connect.
- `src/api/models.py` — ORM tables mirroring `schemas.py`: `cases`, `vessel_tracks`,
  `ais_points` (hypertable-shaped, indexed on `(mmsi, timestamp)`), `phi_meta`. Use
  `Geography(POINT)` / `Geography(LINESTRING)` columns — recidivism lookups are one
  `ST_DWithin`, don't build that by hand.
- `src/api/main.py` — FastAPI app, health check, CORS for the Vite dev server.

### Day 2 — AIS ingest
- Download MarineCadastre AIS, Gulf of Mexico, one month (~2 GB CSV):
  `marinecadastre.gov/accessais/`.
- `src/ais/ingest.py` — CSV → cleaned `AISPoint` rows: parse timestamps as UTC, drop
  impossible speeds (>60 kt), dedupe by `(mmsi, timestamp)`.
- `src/ais/tracks.py` — group into `VesselTrack`, detect gaps > configured threshold,
  **interpolate across them and inflate `position_std_km`** — never silently. This is a
  named requirement in the master context (M6 fallback) — do not skip it.
- `src/ais/synthetic.py` — generator for Indian-EEZ demo traffic: draw from the real Gulf
  of Mexico speed/heading/gap distributions, replay in an Indian bbox. The PS explicitly
  permits this (Section 12.5) — keep it statistically honest, not just visually plausible.

### Day 3 — API surface
- `src/api/routes/cases.py` — `GET /cases`, `GET /cases/{id}`, `POST /cases` (kick off a
  pipeline run as a Celery job).
- `src/api/routes/detect.py` — `POST /detect` (scene → NETRA → `SlickDetection`).
- `src/api/routes/attribute.py` — `POST /attribute` (detection + tracks → NYAYA).
- `src/api/routes/forecast.py` — `POST /forecast` (PRAVAAH).
- `src/api/routes/judge.py` — **`POST /cases/{id}/toggle-transponder`** — sets
  `VesselTrack.transponder_active=False` for one MMSI and re-runs attribution. This is
  Demo Moment 3, the highest-leverage 90 seconds in the whole build. Build it early and
  make it fast — sub-2-second round trip or the moment dies on stage.
- `src/api/worker.py` — Celery app, one task per pipeline stage, chained.

### Day 4 — hand off to P1
- Real `VesselTrack` objects from Gulf of Mexico AIS, queryable by bbox+time window
  (`AIS_WINDOW_BEFORE_HOURS` / `AFTER_HOURS`), delivered to P1 for the go/no-go rebuild
  and the hero case.
- WebSocket endpoint (`src/api/routes/ws.py`) streaming job progress — P5 needs this for
  the particle animation to feel live rather than a spinner.

### Day 5 — SMRITI
- `src/smriti/store.py` — persist every `Case` with its Φ and outcome.
- `src/smriti/recidivism.py` — spatial nearest-neighbour: given a new Φ, find prior cases
  whose fields overlap the same vessel or corridor. One `ST_DWithin` query, no embeddings.
- `src/smriti/hotspots.py` — pre-computed static heatmap of discharge corridors by time-
  of-day, for Demo Moment 5. Build it from simulated case history if real cases are thin.

### Day 6 — ABHIYAN (greedy) + PRAMAN wiring
- `src/abhiyan/tasking.py` — given Φ, three hardcoded assets (Dornier / OPV / station
  boat) with endurance and speed, compute the search box covering the most Φ mass
  reachable within endurance, greedily. Not an LP — Section 16.5 explicitly permits this.
- `src/praman/manifest.py` — assemble `EvidenceManifest`: scene IDs, model + forcing
  versions (read the sidecars P3 writes), Φ checksum (`sha256`), posterior snapshot.
  Deterministic serialisation — same case, same manifest, byte for byte.

### Day 7 — hardening
- Load test the toggle-transponder endpoint — it will be clicked live in front of judges.
- `DEMO_MODE` short-circuit: serve cached `Case` JSON instead of running Celery jobs.
- Package cases, scenes, forcing, and model weights onto the portable SSD with P6.

---

## Files You Create

| Path | Purpose |
|---|---|
| `src/api/db.py` | SQLAlchemy engine/session, PostGIS bootstrap |
| `src/api/models.py` | ORM tables |
| `src/api/main.py` | FastAPI app |
| `src/api/worker.py` | Celery app + task chain |
| `src/api/routes/{cases,detect,attribute,forecast,judge,ws}.py` | REST + WS surface |
| `src/ais/ingest.py` | MarineCadastre CSV → `AISPoint` |
| `src/ais/tracks.py` | Points → `VesselTrack`, gap handling |
| `src/ais/synthetic.py` | Indian-EEZ synthetic traffic generator |
| `src/smriti/store.py` | Case persistence |
| `src/smriti/recidivism.py` | Spatial NN lookup |
| `src/smriti/hotspots.py` | Static corridor heatmap |
| `src/abhiyan/tasking.py` | Greedy asset tasking |
| `src/praman/manifest.py` | Evidence manifest assembly |

## API routes (exact)

```
POST   /detect                          scene_id, wind_grid_id -> list[SlickDetection]
POST   /attribute                       slick_id, phi_id, mmsi_window -> AttributionResult
POST   /forecast                        slick_id -> ForwardForecast
GET    /cases                           -> list[Case] (summary)
GET    /cases/{id}                      -> Case (full)
POST   /cases                           detection -> kicks off pipeline, returns case_id
POST   /cases/{id}/toggle-transponder   {mmsi} -> re-run AttributionResult
GET    /ws/cases/{id}/progress          WebSocket, pipeline stage events
```

## Interfaces

- **PRODUCE:** `list[VesselTrack]` (→ P1, P2), `Case` persistence (→ P5 via REST),
  `AssetTasking`, `EvidenceManifest`.
- **CONSUME:** `SlickDetection` (P2), `PhiFieldMeta` (P3), `AttributionResult` (P1),
  `ForwardForecast` (P3).
- **NEED FROM:** nothing blocking — you can build the entire spine against
  `schemas.py` alone. Real detections/Φ/attribution arrive day 4+ from P1–P3.

## Claude Code Prompt

```
Read CLAUDE.md and tasks/P4_BACKEND.md. You are P4, backend. You own the FastAPI API,
the AIS ingest pipeline, PostGIS persistence, SMRITI, and greedy ABHIYAN tasking.

Import all shared types from src.common.schemas. Do not redefine them. Use
src.common.config.get_settings() for all connection strings and paths. Python 3.10+,
type hints, SQLAlchemy 2.0 style.

Start with src/api/db.py and src/api/models.py now — SQLAlchemy engine/session and
ORM tables mirroring schemas.py (cases, vessel_tracks, ais_points, phi_meta), using
Geography columns for spatial fields. Then src/api/main.py with a health check.
```

## If Claude Is Offline

- MarineCadastre AIS format: `MMSI, BaseDateTime, LAT, LON, SOG, COG, Heading, VesselName,
  IMO, CallSign, VesselType, Status, Length, Width, Draft, Cargo, TransceiverClass`.
- PostGIS spatial index: `CREATE INDEX ... USING GIST (geom)`, query with
  `ST_DWithin(geom, ST_MakePoint(lon,lat)::geography, radius_m)`.
- Celery quick start: `celery.py` defines `celery_app = Celery("varuna", broker=REDIS_URL,
  backend=REDIS_URL)`; tasks are plain functions decorated `@celery_app.task`.
- FastAPI WebSocket: `@app.websocket("/ws/...")`, `await websocket.accept()`, loop
  `await websocket.send_json(...)`.
