# ROLE 02 — Data / Backend

**Owns:** PRAHARI · Data Guard · source adapters · AIS · PostGIS · MinIO · FastAPI · Event Spine · Case Management · PRAMAN

You own the trust boundary. Every external byte that reaches a scientific module passed
through your code, and every claim the system makes is only as defensible as the
provenance you attached. Read `LLM_IMPLEMENTATION_GUIDE.md` §10 and
`FAILURE_THREAT_MATRIX.md` §1–2, §7.

---

## The rule that defines this role

> **No external service response ever enters scientific inference directly.**

Adapter → Ingestion Gate → Data Guard → enveloped payload. A scientific module that can
call `httpx` is an architecture violation, not a shortcut.

---

## Day-by-day

### Day 1 — foundation
- `docker compose up postgres redis minio` must work end to end. There is currently **no
  Dockerfile** — write `infra/docker/Dockerfile` first (see `DEPLOYMENT.md`).
- `apps/api/db.py` — SQLAlchemy 2.0 engine/session, PostGIS extension on connect.
- `apps/api/models.py` — ORM: `cases`, `case_state`, `vessel_tracks`, `ais_points`
  (indexed `(mmsi, timestamp)`), `phi_meta`, `events`, `evidence_manifests`, `missions`.
  Use `Geography(POINT/LINESTRING)` — recidivism is one `ST_DWithin`.
- `apps/api/main.py` — FastAPI, health check, CORS for Vite.
- Alembic init + first migration.

### Day 2 — Data Guard + AIS
- `packages/varuna_data_guard/checks.py` — one function per check, each returning
  `(passed, AnomalyFlag | None, detail)`: schema · units · CRS · temporal consistency ·
  spatial bounds · completeness · freshness · physical plausibility · statistical outliers.
- `packages/varuna_data_guard/trust.py` — combine check results → `TrustState` +
  `influence_weight`. **Unknown check result → DEGRADED, never TRUSTED. Never fail open.**
- `packages/varuna_data_guard/quarantine.py` — retain raw, zero influence.
- `packages/varuna_source_adapters/ais.py` — MarineCadastre CSV → `AISPoint`; drop
  impossible speeds; dedupe `(mmsi, timestamp)`.
- `packages/varuna_source_adapters/tracks.py` — group → `VesselTrack`; detect gaps;
  **interpolate AND inflate `position_std_km`** — never silently.
- Deliver real `VesselTrack` objects to ROLE 01.

### Day 3 — adapters + API surface
- `packages/varuna_source_adapters/{cmems,era5,copernicus,base}.py` — auth, timeout,
  bounded retry with backoff, rate limit, response validation, **raw preservation to
  MinIO**, cache keyed by bbox+time hash, JSON sidecar with product ID + version.
- Fallback chain: live → cache → snapshot → climatology, each stamping `degradation_state`.
- Routes: `POST /detect`, `POST /attribute`, `POST /forecast`, `GET /cases`,
  `GET /cases/{id}`, `POST /cases`, `POST /cases/{id}/toggle-transponder`,
  `GET /events/{case_id}`, `GET /sse/cases/{id}` (SSE, not WebSocket — see stack).

### Day 4 — Event Spine + Case Management
- `packages/varuna_domain/events.py` — append-only spine, monotonic sequence per case.
  Out-of-order events are parked, never applied (threat G-01).
- `packages/varuna_domain/cases.py` — `CaseStateVector` transitions. **Call
  `check_case_invariants()` on every write**; a violation is a P0 bug, not a warning.
- `packages/varuna_data_guard/flow_inspection.py` — the five boundary checks:
  `Data→NETRA`, `NETRA→PRATIVARTAN`, `PRATIVARTAN→NYAYA`, `NYAYA→ABHIYAN`,
  `ABHIYAN→ActionGateway`. Φ normalisation check lives here (threat P-08).

### Day 5 — PRAMAN
- `packages/varuna_praman/manifest.py` — raw refs, model versions, forcing versions,
  parameters, Φ hash, posterior snapshot, human decisions **stored separately from AI
  recommendations**, chain of custody, `manifest_checksum`.
- **Deterministic serialisation**: same case ⇒ byte-identical manifest. Sorted keys,
  fixed separators. Test it (threat G-03).
- Append-only enforcement — writes to existing artifacts rejected (threat G-02).

### Day 6 — PRAHARI + cross-source
- `packages/varuna_data_guard/cross_source.py` — source drift, cross-source consistency,
  and the **source dependency registry** (CMEMS and ERA5 share upstream models — treat
  their agreement as weaker evidence than it appears; threat S-07).
- `apps/worker/prahari.py` — scheduler → scene discovery → queue → preprocess → NETRA →
  case creation. Prototype = historical replay over a scoped region from cached sources.

### Day 7 — integration only
- CASE-0001 end to end. `DEMO_MODE=true` serves frozen artifacts.
- Load-test `toggle-transponder` — it is clicked live in front of judges.

---

## Files you create

```
infra/docker/Dockerfile
apps/api/{main,db,models,deps,security}.py
apps/api/routes/{cases,detect,attribute,forecast,judge,events,sse}.py
apps/worker/{celery_app,tasks,prahari}.py
packages/varuna_data_guard/{checks,trust,quarantine,cross_source,flow_inspection}.py
packages/varuna_source_adapters/{base,cmems,era5,copernicus,ais,tracks,synthetic_ais}.py
packages/varuna_domain/{events,cases,policy}.py
packages/varuna_praman/{manifest,store,hashing}.py
db/migrations/
tests/{integration,robustness}/test_data_guard_*.py
```

## Interfaces

- **PRODUCE:** enveloped payloads (all with `Provenance` + `TrustState`),
  `list[VesselTrack]`, `EvidenceManifest`, case state, event stream.
- **CONSUME:** `SlickDetection`, `PhiField`, `AttributionResultV2` for persistence.
- **NEED:** ROLE 01 by day 1 — mock Φ to test serialisation. ROLE 04 by day 1 — compose stack.

## API routes (exact)

```
POST /detect                        scene_id, wind_grid_id  → list[SlickDetection]
POST /attribute                     slick_id, phi_id, window → AttributionResultV2
POST /forecast                      slick_id                 → ForwardForecast
GET  /cases                                                  → list[Case summary]
GET  /cases/{id}                                             → Case (full)
POST /cases                         detection                → case_id (queues pipeline)
POST /cases/{id}/toggle-transponder {mmsi}                   → AttributionResultV2
GET  /events/{case_id}                                       → ordered event log
GET  /sse/cases/{id}                                         → SSE progress stream
```

## Acceptance criteria

- [ ] `docker compose up` works from a clean clone
- [ ] Every `AnomalyFlag` has a detector + robustness test
- [ ] Data Guard fails **closed** — unknown → DEGRADED
- [ ] Raw artifacts preserved and never overwritten; hashes verified
- [ ] `check_case_invariants()` called on every case write
- [ ] Event ordering enforced per case
- [ ] Manifest byte-identical on re-run
- [ ] No adapter makes a live call in CI (recorded fixtures only)

## Do NOT touch

`packages/varuna_nyaya`, `varuna_netra`, `varuna_prativartan` internals; `apps/web`;
`varuna_contracts` without an ADR.

## Claude Code prompt

```
Read LLM_IMPLEMENTATION_GUIDE.md and tasks/ROLE_02_DATA_BACKEND.md. You are ROLE 02,
data/backend, owning the trust boundary: source adapters, Data Guard, AIS, PostGIS,
MinIO, FastAPI, Event Spine, Case Management, PRAMAN.

Hard rule: no external service response enters scientific inference directly. Adapter →
Ingestion Gate → Data Guard → enveloped payload. Data Guard fails CLOSED (unknown →
DEGRADED, never TRUSTED).

Import all types from varuna_contracts. Python 3.12, SQLAlchemy 2.0 style, full type
hints, structlog with case_id bound.

Start with infra/docker/Dockerfile — there is currently no Dockerfile, so
docker-compose.yml is broken. Then apps/api/db.py and apps/api/models.py with PostGIS
Geography columns, then apps/api/main.py with a health check.
```
