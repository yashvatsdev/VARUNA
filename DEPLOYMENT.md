# DEPLOYMENT.md
## VARUNA GRID v2 — deployment and operations

> **Status:** the compose stack has been written but **never started** — no image has been
> built (`SETUP_STATUS.md`). Treat the first `make up` as a task, not a formality.

---

## 1. Topology

Single node, Docker Compose. Air-gappable by design.

```
Browser ──HTTPS──► Nginx ──► apps/web   (React SPA, static)
                        └──► apps/api   (FastAPI, JWT+RBAC)
                                  ├──► PostgreSQL + PostGIS   cases, tracks, missions, events
                                  ├──► MinIO                  scenes, Φ, raw evidence
                                  └──► Redis ──► apps/worker (default queue)
                                            └──► worker-physics (OpenDrift, own image)
                    OTel Collector ──► Prometheus ──► Grafana
                                   └──► Loki ────────┘
                    MLflow (profile: mlops)
```

Two worker images on purpose: OpenDrift ships through conda-forge and pip resolution is
unreliable, so the physics worker uses `Dockerfile.physics` (micromamba) while the API and
default worker stay on a slim pip image.

---

## 2. First run

```bash
cp .env.example .env
# set POSTGRES_PASSWORD, MINIO_SECRET_KEY, JWT_SECRET, and Copernicus/CDS credentials

make up-infra          # postgres + redis + minio, with healthchecks
make migrate           # alembic upgrade head
make seed              # CASE-0001 fixture
make up                # + api and worker
curl -fsS localhost:8000/health
```

Physics worker (large image, build once):

```bash
docker compose --profile physics up -d --build
```

Frontend dev server: `docker compose --profile web up`
MLflow: `docker compose --profile mlops up -d`

---

## 3. Environment variables

All config flows through `pydantic-settings`. **Never hardcode.** `.env` is gitignored;
`.env.example` is the committed template.

| Group | Keys |
|---|---|
| Infra | `DATABASE_URL` `REDIS_URL` `MINIO_ENDPOINT` `MINIO_ACCESS_KEY` `MINIO_SECRET_KEY` `MINIO_BUCKET` |
| Paths | `DATA_DIR` `FORCING_DIR` `SCENE_DIR` `CACHE_DIR` `OUTPUT_DIR` `MODEL_DIR` |
| Models | `NETRA_MODEL_PATH` `CHHAYA_MODEL_PATH` `CALIBRATION_MODEL_PATH` |
| Φ | `PHI_N_PARTICLES` `PHI_N_ENSEMBLE` `PHI_DT_SECONDS` `PHI_GRID_NX` `PHI_GRID_NY` `PHI_TIME_BIN_HOURS` |
| NYAYA | `NYAYA_CORRIDOR_KM` `NYAYA_INCONCLUSIVE_ENTROPY` `NYAYA_MIN_POSTERIOR_FOR_NAME` |
| Security | `JWT_SECRET` `JWT_ALGORITHM` `ACCESS_TOKEN_TTL_MIN` |
| Ops | `API_HOST` `API_PORT` `LOG_LEVEL` `OTEL_EXPORTER_OTLP_ENDPOINT` `DEMO_MODE` |
| External | `COPERNICUSMARINE_SERVICE_USERNAME/PASSWORD` `CDSAPI_URL` `CDSAPI_KEY` |

---

## 4. Production differences

`docker-compose.prod.yml` overrides:

- `--reload` removed; uvicorn behind gunicorn with 2–4 workers
- Source bind-mounts removed (code baked into the image)
- Nginx terminates TLS, sets HSTS/CSP, serves the built SPA
- Postgres tuned (`shared_buffers`, `work_mem`) and backed up on a schedule
- Log level `INFO`; structured JSON to Loki
- Resource limits per service
- Restart policy `unless-stopped`

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 5. Database

```bash
alembic revision --autogenerate -m "add mission table"
alembic upgrade head
alembic downgrade -1
```

PostGIS extension is enabled on connect. Indexes that matter:
`ais_points(mmsi, timestamp)` · GIST on every `Geography` column ·
`cases(created_at)` · `events(case_id, sequence)`.

**Backups:** `pg_dump` nightly; MinIO bucket mirrored. Raw evidence is append-only and must
survive any restore — verify by restoring to a scratch instance, not by assuming.

---

## 6. Air-gapped / demo deployment

`DEMO_MODE=true` serves frozen artifacts and makes **zero external calls**.

Pre-stage on the portable SSD:

```
docker images (api, physics, postgres, redis, minio)  → docker save
models/            trained weights, TorchScript exports
data/forcing/      cached CMEMS + ERA5 NetCDF
data/scenes/       demo SAR scenes
data/cache/        pre-computed Φ + frozen AttributionResults
apps/web/tiles/    self-hosted MBTiles basemap (tileserver-gl)
db/seed/           CASE-0001 dump
```

```bash
bash infra/scripts/restore_ssd.sh /media/ssd
make demo
make verify-offline     # asserts no external network call
```

> **Restore and run on a second machine before travelling.** An untested restore is not a
> backup. This is the single most common way teams lose a demo.

---

## 7. Observability

| Signal | Path | Watch |
|---|---|---|
| Logs | structlog → Loki → Grafana | `case_id` bound on every line in a case's path |
| Traces | OpenTelemetry → collector | Φ computation span duration |
| Metrics | Prometheus → Grafana | queue depth, Φ runtime, gate rejection rate, adapter failure rate |

**Alert-worthy conditions:** Φ runtime > 5 min · validity-gate rejection rate spike ·
adapter fallback rate > 10% · quarantine rate > 5% · any case-invariant violation
(**always a P0 bug**) · Celery queue depth growing unboundedly.

---

## 8. Runbooks

Keep these in `docs/runbooks/` as they are written:

| Scenario | First action |
|---|---|
| Φ computation hangs | Check physics worker logs; verify forcing cache present; reduce M |
| Adapter failing repeatedly | Check credentials, then rate limit; confirm fallback chain engaged |
| Quarantine rate spike | Likely upstream schema change — inspect raw artifacts, do not relax the check |
| Case-invariant violation | **P0.** Identify the writing subsystem; do not patch the invariant |
| Disk full | Φ fields are the growth term. Archive old cases. **Never delete raw evidence.** |
| Demo failure | `DEMO_MODE` → replay mode → recorded video, in that order |

---

## 9. Security posture

- JWT auth; RBAC roles: `viewer`, `analyst`, `officer`, `admin`. **Only `officer` may
  authorize a mission.**
- Argon2 password hashing.
- Secrets via environment only; `bandit`, `pip-audit`, Trivy, and a secret scan in CI.
- Non-root container user (uid 10001).
- No inbound internet required in air-gapped mode.
- Full detail in `SECURITY.md`.

---

## 10. Rollback

```bash
docker compose down
git checkout <previous-tag>
docker compose up -d --build
alembic downgrade <revision>    # only if the migration is genuinely reversible
```

Model rollback is a registry operation: repoint `NETRA_MODEL_PATH` at the previous
promoted version. Because `model_version` is stamped on every output, past decisions
remain attributable to the model that actually made them.
