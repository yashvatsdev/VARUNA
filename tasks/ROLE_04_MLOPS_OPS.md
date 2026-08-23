# ROLE 04 — MLOps / Ops

**Owns:** PRAVAAH · ABHIYAN · missions · alerts · Docker · Celery · Redis · MLflow · CI/CD · observability · deployment · integration · SMRITI pipeline

You own whether any of this actually runs, and you own the two gates that stand between a
recommendation and a physical action. Read `LLM_IMPLEMENTATION_GUIDE.md` §10 and
`FAILURE_THREAT_MATRIX.md` §5–7.

---

## The rule that defines this role

> **No operational action bypasses the authorization gate.**

`MissionRecord.transition(ASSIGNED)` raises without `human_approved_by`. The Action
Gateway consumes a `ValidityGateResult`, never a raw `AttributionResultV2`. And SMRITI
never closes a learning loop without a human approving the new model version.

---

## Day-by-day

### Day 1 — make the stack real
- `infra/docker/Dockerfile` (with ROLE 02) — Python 3.12 slim, GDAL/PROJ system deps,
  non-root user. **`docker-compose.yml` currently references `build: .` with no
  Dockerfile — the stack does not start. Fix this first.**
- `docker-compose.yml` + `docker-compose.prod.yml`, `infra/nginx/`, `Makefile`.
- `.github/workflows/ci.yml` — ruff, mypy, pytest (unit+contract), bandit, pip-audit.
- **Install OpenDrift and verify backward simulation works** — ROLE 01 is blocked on this
  by day 2. `conda install -c opendrift -c conda-forge opendrift` if pip resolution fails.

### Day 2 — workers + observability
- `apps/worker/celery_app.py` — Celery + Redis, one task per pipeline stage, chained.
- OpenTelemetry on API and worker; Prometheus metrics; Grafana + Loki in compose.
- Bind `case_id` on every span and log line in a case's path.

### Day 3 — PRAVAAH
- `packages/varuna_pravaah/forecast.py` — forward drift, 24/48/72 h. `OpenOil` is
  appropriate here (weathering is fine forward; it is only irreversible backward).
- `packages/varuna_pravaah/landfall.py` — GSHHG coastline intersection → **named** beach.
  Landfall is an **interval with probability**, never a point time.
- `packages/varuna_pravaah/exposure.py` — sensitive zones, fishing grounds.

### Day 4 — ABHIYAN
- `packages/varuna_abhiyan/feasibility.py` — **filter first**: range, endurance, sea state,
  crew hours. An infeasible asset is excluded with a stated reason, never ranked low.
- `packages/varuna_abhiyan/value.py` — value matrix over Φ mass reachable per asset-hour.
- `packages/varuna_abhiyan/assign.py` — **exact optimisation** (`scipy.optimize.linear_sum_assignment`).
  At our case/asset counts exact is cheap and explainable. **No RL.**
- `packages/varuna_abhiyan/explain.py` — why this asset, why this box, what was rejected.

### Day 5 — missions + alerts
- `packages/varuna_missions/` — FSM wrapper, reservation (prevents double-booking),
  approval capture. AI recommendation and human decision stored **separately**.
- `packages/varuna_alerts/providers.py` — `NotificationProvider` interface; Web, Email,
  SMS, WhatsApp, CAP. **Every provider declares `is_simulated`** — enforced in schema
  (threat L-04).
- `packages/varuna_alerts/router.py` — materiality → role router → content policy →
  freshness → channel adapter → delivery log, with idempotency keys.

### Day 6 — SMRITI pipeline
- `packages/varuna_smriti/{history,recurrence,corridors,similarity}.py` — PostGIS queries.
- `packages/varuna_smriti/retraining.py` — **the controlled loop**:
  `outcome → candidate dataset → offline experiment → validation → HUMAN APPROVAL →
  new model version → deployment`. There must be **no code path** that updates a model
  from field outcomes without that approval (threat G-07). Write the test that proves it.
- MLflow registry; `model_version` stamped on every inference output (threat G-08).

### Day 7 — integration + rehearsal
- CASE-0001 end to end in Docker. Failure-injection pass over every P0 row.
- `DEMO_MODE=true` verified: no external calls, frozen artifacts served.
- Portable SSD: images, weights, forcing, tiles. **Restore and test on a second machine.**

---

## Files you create

```
infra/docker/Dockerfile
infra/nginx/nginx.conf
infra/monitoring/{prometheus.yml,grafana/,loki.yml,otel-collector.yaml}
infra/scripts/{seed_case_0001.sh,cache_forcing.py,restore_ssd.sh}
Makefile · docker-compose.yml · docker-compose.prod.yml
.github/workflows/{ci.yml,security.yml}
apps/worker/{celery_app,tasks}.py
packages/varuna_pravaah/{forecast,landfall,exposure}.py
packages/varuna_abhiyan/{feasibility,value,assign,explain}.py
packages/varuna_missions/{fsm,authorization,store}.py
packages/varuna_alerts/{providers,router,materiality,delivery}.py
packages/varuna_smriti/{history,recurrence,corridors,similarity,retraining}.py
tests/{integration,e2e,robustness}/
```

## Interfaces

- **PRODUCE:** `ForwardForecast`, `LandfallPrediction`, `AssetTasking`, `MissionRecord`,
  delivery logs, the running platform.
- **CONSUME:** `ValidityGateResult` (never a raw attribution), `PhiField`, `Case`.
- **NEED:** ROLE 01 by day 4 — `ValidityGateResult`. ROLE 02 by day 3 — case persistence + events.

## Makefile targets

```
make up / down / logs        docker compose lifecycle
make migrate                 alembic upgrade head
make seed                    load CASE-0001
make test                    unit + contract (no services)
make test-integration        needs compose up
make test-scientific         seeded numerical regression
make test-robustness         failure injection
make lint / typecheck / security
make demo                    DEMO_MODE=true, frozen artifacts
```

## Acceptance criteria

- [ ] `docker compose up` works from a clean clone
- [ ] CI green: ruff, mypy, pytest, bandit, pip-audit
- [ ] OpenDrift verified backward-capable (day 1)
- [ ] ABHIYAN never returns an infeasible assignment
- [ ] `ASSIGNED` impossible without `human_approved_by` (contract-tested ✅)
- [ ] Every alert provider declares `is_simulated`
- [ ] **No code path retrains a model without human approval** — test proves it
- [ ] `model_version` stamped on every inference output
- [ ] `DEMO_MODE=true` makes zero external calls
- [ ] Full restore works on a second machine

## Do NOT touch

Scientific internals in `varuna_netra`, `varuna_prativartan`, `varuna_nyaya`;
`apps/web`; `varuna_contracts` without an ADR.

## Claude Code prompt

```
Read LLM_IMPLEMENTATION_GUIDE.md and tasks/ROLE_04_MLOPS_OPS.md. You are ROLE 04,
MLOps/Ops, owning PRAVAAH, ABHIYAN, missions, alerts, Docker, Celery, MLflow, CI/CD,
observability, deployment, and the SMRITI retraining pipeline.

Hard rules: no operational action bypasses the authorization gate (ASSIGNED requires
human_approved_by); the Action Gateway consumes ValidityGateResult, never a raw
AttributionResultV2; SMRITI has no online self-training path — outcome to new model
version always crosses a human approval gate. ABHIYAN uses exact optimisation, not RL.

Import all types from varuna_contracts. Python 3.12, full type hints.

Start with infra/docker/Dockerfile — docker-compose.yml references `build: .` but no
Dockerfile exists, so the stack cannot start. Python 3.12-slim, GDAL/PROJ system deps,
non-root user, installs the project via pyproject.toml. Then fix docker-compose.yml and
add the Makefile.
```
