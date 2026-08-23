# LLM_IMPLEMENTATION_GUIDE.md
## Universal context packet for any coding LLM working on VARUNA GRID v2

**Read this file + your ROLE file + `packages/varuna_contracts/` before writing code.**
That is sufficient context. You do not need the originating conversation.

---

## 1. Mission

VARUNA GRID detects marine oil spills in Sentinel-1 SAR, reconstructs **where and when**
the oil was released as a probability field, and scores AIS vessel tracks against that
field to produce a **calibrated posterior** over suspects — including an explicit
hypothesis that the culprit was not broadcasting at all.

It then forecasts landfall, recommends which asset to launch, and seals a prosecutable
evidence file.

**The product is the API**, not the map. Strip the UI and what remains is:
ensemble reverse advection → origin field Φ(x,y,t) → path-integral trajectory scoring →
normalised posterior with a latent-source term → calibration → gated operational decision.

---

## 2. Source-of-truth hierarchy

When two documents disagree, the higher entry wins.

| Rank | Source | Authority over |
|---|---|---|
| 1 | `packages/varuna_contracts/` (code) | All data shapes, states, invariants |
| 2 | `docs/adr/` | Architectural decisions and their rationale |
| 3 | `ARCHITECTURE_V2.md` | Module boundaries, planes, data flow |
| 4 | `FAILURE_THREAT_MATRIX.md` | Required failure behaviour |
| 5 | `LLM_IMPLEMENTATION_GUIDE.md` (this) | Module contracts, coding rules |
| 6 | `tasks/ROLE_*.md` | Per-person scope and sequencing |
| 7 | `README.md`, `CLAUDE.md` | Orientation only |
| 8 | `VARUNA_MASTER_CONTEXT.md` | Domain/strategy background (v1-era; architecture is superseded) |

**The repository is the authority on what is implemented.** Documentation may describe
intent. Never infer that something exists because a document says "complete".

---

## 3. Architecture in one screen

```
                        ┌──────────── GOVERNANCE PLANE ────────────┐
                        │ Event Spine · PRAMAN · audit · lineage   │
                        │ observability · security · versioning    │
                        └──────────────────────────────────────────┘
                                          ▲ (every step emits)
EXTERNAL          ┌───────────────── DATA PLANE ─────────────────┐
Sentinel-1  ─┐    │                                              │
CMEMS       ─┤    │  Source Adapter → Ingestion Gate             │
ERA5        ─┼───▶│        ↓                                     │
AIS         ─┤    │  DATA GUARD  (trust: TRUSTED/DEGRADED/       │
xView3      ─┘    │               CONFLICTED/QUARANTINED)        │
                  │        ↓                                     │
                  │  Flow / Integrity Inspection                 │
                  │        ↓                                     │
                  │  NETRA → PRATIVARTAN → Φ diagnostics         │
                  │        ↓                    ↓                │
                  │  NYAYA ←──────────────── CHHAYA              │
                  │        ↓                                     │
                  │  ★ VALIDITY / UNCERTAINTY GATE ★             │
                  │        ↓                                     │
                  │  PRAVAAH → Case Intelligence → ABHIYAN       │
                  │        ↓                                     │
                  │  Mission FSM → ★ AUTHORIZATION ★ → HUMAN     │
                  │        ↓                                     │
                  │  Action Gateway → Field Outcome → SMRITI     │
                  └──────────────────────────────────────────────┘
                                          ▲
                        ┌──────────── CONTROL PLANE ───────────────┐
                        │ source trust · policy · thresholds ·     │
                        │ RBAC · versions · feature flags ·        │
                        │ model registry · recovery                │
                        └──────────────────────────────────────────┘
```

The two ★ gates are **mandatory chokepoints**. No path to an operational action may
bypass them.

---

## 4. The twelve architectural invariants

These are enforced in code (`tests/contract/`) and are not negotiable without an ADR.

1. **Fail safely, not silently.** Every failure produces a typed, logged, degraded result — never a silent default, never a swallowed exception.
2. **Raw evidence is never overwritten.** Derived artifacts reference raw ones by `provenance.raw_artifact_refs`.
3. **Trust ≠ confidence.** Trust is about the source (Data Guard). Confidence is about the measurement (model). Never collapse them into one number.
4. **Uncertainty propagates.** Use `EvidenceEnvelope.derive()`. It refuses to upgrade trust/validity/degradation.
5. **Every subsystem consumes provenance and emits validity metadata.** No bare payloads across module boundaries.
6. **No external service bypasses an adapter.** Never call `httpx` to an external API from inside a scientific module.
7. **No operational action bypasses the authorization gate.** `MissionRecord.transition(ASSIGNED)` raises without `human_approved_by`.
8. **INCONCLUSIVE is a valid outcome.** Returning it is success, not failure.
9. **Human decisions and AI recommendations are stored separately.** Never merge `recommended_by_system` into `human_approved_by`.
10. **Bounded Evidence Influence, not value mutation.** Down-weight suspicious data via `influence_weight`; never silently clip or "correct" the value itself.
11. **SMRITI never self-trains online.** Outcome → dataset → offline experiment → validation → human approval → new version. No closed loop.
12. **Scientific claims stay honest.** See §12.

---

## 5. Repository layout

```
packages/varuna_contracts/     ★ THE locked contract — import from here, never redefine
packages/varuna_domain/          case logic, invariants, policy evaluation
packages/varuna_data_guard/      trust scoring, anomaly detection, quarantine
packages/varuna_source_adapters/ CMEMS, ERA5, Copernicus, AIS, xView3 adapters
packages/varuna_geospatial/      CRS, distance, bbox, coastline utilities
packages/varuna_netra/           slick detection + look-alike rejection + age prior
packages/varuna_prativartan/     reverse advection ensemble → Φ
packages/varuna_nyaya/           path integral, priors, latent hypothesis, posterior
packages/varuna_chhaya/          dark-vessel investigation (xView3)
packages/varuna_pravaah/         forward drift, landfall, exposure
packages/varuna_abhiyan/         feasibility → value matrix → assignment
packages/varuna_missions/        mission FSM, authorization
packages/varuna_alerts/          notification providers, materiality, routing
packages/varuna_praman/          evidence preservation, manifests, hashing
packages/varuna_smriti/          history, recurrence, corridors, retraining pipeline
apps/api/                        FastAPI
apps/worker/                     Celery
apps/web/                        React + Vite + MapLibre + deck.gl
tests/{unit,contract,integration,scientific,robustness,e2e}/
experiments/                     go_nogo, convergence, forcing_bias, baselines, ...
docs/adr/                        architecture decision records
```

Imports are absolute: `from varuna_contracts import EvidenceEnvelope`.

---

## 6. The Evidence Envelope (read `packages/varuna_contracts/evidence.py`)

Every major subsystem output carries one:

```python
EvidenceEnvelope(
    artifact_id, case_id, parent_artifact_ids,
    produced_by, model_version, processing_version, created_at,
    crs, units,
    provenance,            # source_id, source_version, raw_artifact_refs, adapter_id
    trust,                 # TRUSTED | DEGRADED | CONFLICTED | QUARANTINED
    influence_weight,      # 0..1, capped by trust.max_influence
    quality,               # completeness, freshness, ood_score, model_confidence
    uncertainty,           # representation, mean/std/interval, entropy, sensitivity
    calibration_state,     # CALIBRATED | UNCALIBRATED | OUT_OF_DOMAIN | N/A
    validity_state,        # VALID | DEGRADED | RESTRICTED | INCONCLUSIVE
    degradation_state,     # NOMINAL | FALLBACK_SOURCE | REDUCED_ENSEMBLE | ...
    anomaly_flags, content_hash,
)
```

**Always build downstream envelopes with `.derive()`:**

```python
out_env = phi.envelope.derive(
    artifact_id=f"attr-{case_id}",
    produced_by="nyaya",
    also_from=[track_env, chhaya_env],
    model_version=CALIBRATION_VERSION,
    uncertainty=UncertaintyBlock(representation="samples", entropy=h),
    calibration_state=CalibrationState.CALIBRATED,
)
```

Never hand-construct a downstream envelope with better trust than its inputs. `derive()`
makes that structurally impossible; bypassing it is a review-blocking defect.

---

## 7. Module dependency graph

```
varuna_contracts   ← (everything; depends on nothing)
varuna_geospatial  ← contracts
varuna_domain      ← contracts
varuna_source_adapters ← contracts, geospatial
varuna_data_guard  ← contracts, geospatial
varuna_netra       ← contracts, geospatial, data_guard
varuna_prativartan ← contracts, geospatial, data_guard, source_adapters
varuna_chhaya      ← contracts, geospatial
varuna_nyaya       ← contracts, geospatial, domain          (NOT netra, NOT prativartan)
varuna_pravaah     ← contracts, geospatial, source_adapters
varuna_abhiyan     ← contracts, domain
varuna_missions    ← contracts, domain
varuna_alerts      ← contracts, domain
varuna_praman      ← contracts
varuna_smriti      ← contracts, domain
apps/*             ← any package
```

**No cycles.** NYAYA takes a `PhiField` object, not a PRATIVARTAN import — that is what
makes it testable against synthetic Φ without the physics engine installed.

---

## 8. Coding standards

- Python **3.12**. Full type hints on every public function. `from __future__ import annotations`.
- **Pydantic v2** for all boundary data. Plain dataclasses/NumPy internally is fine.
- **UTC tz-aware datetimes only.** A naive datetime crossing a module boundary is a bug.
- **WGS84, (lon, lat)** ordering everywhere. km, km², knots (AIS), m/s (forcing).
- `structlog` — structured events, never `print`. Bind `case_id` and `artifact_id`.
- Absolute imports. Line length 100. `ruff` + `mypy` clean.
- Seed every stochastic path explicitly; scientific results must be reproducible.
- Docstrings explain **why**, not what. Skip narration of obvious code.

---

## 9. Forbidden behaviour

Do **not**:

- Redefine any type that exists in `varuna_contracts`.
- Call an external HTTP API outside `varuna_source_adapters`.
- Mutate a value because it looks wrong — down-weight it via `influence_weight`.
- Return a bare `float`/`dict` from a subsystem entry point — return an enveloped model.
- Silently substitute a default on failure (`except: return 0.0`). Degrade explicitly.
- Let an LLM/chatbot compute or alter Φ, posteriors, trust, assignments, or severity.
- Add Kafka, Kubernetes, a service mesh, a vector DB, RAG, an agent framework, or RL for the core — each requires an ADR that will almost certainly be rejected.
- Introduce online self-training anywhere.
- Write a number into a report that did not come from a structured pipeline output.
- Mark work "complete" in documentation without a passing test.

---

## 10. Module contracts

Each entry is the full brief. Build to it.

---

### `varuna_data_guard` — trust boundary

| | |
|---|---|
| **INPUT** | Raw payload + `Provenance` from a source adapter |
| **OUTPUT** | `(payload, EvidenceEnvelope)` with `trust`, `influence_weight`, `anomaly_flags` |
| **DEPENDS** | contracts, geospatial |
| **LIBRARIES** | numpy, scipy, xarray, pydantic |
| **FORBIDDEN** | Modifying payload values; dropping records silently |
| **FAILURE MODES** | Schema drift, unit/CRS mismatch, stale data, correlated source bias, spoofing |
| **FALLBACK** | Unknown check → `DEGRADED`, not `TRUSTED`. Never fail open. |
| **TESTS** | `tests/robustness/test_data_guard_*.py` — inject each anomaly, assert flag + trust |
| **DONE** | Every `AnomalyFlag` has a detector, a test, and a documented trust consequence |

Checks: schema · units · CRS · temporal consistency · spatial consistency · completeness ·
freshness · physical plausibility · statistical outliers · source health · source drift ·
cross-source consistency · source dependency/correlation · suspected manipulation.

---

### `varuna_source_adapters` — the only external boundary

| | |
|---|---|
| **INPUT** | Query (bbox, time range, product id) |
| **OUTPUT** | Raw artifact persisted to object store + `Provenance` |
| **DEPENDS** | contracts, geospatial |
| **LIBRARIES** | httpx, copernicusmarine, cdsapi, minio, xarray |
| **FORBIDDEN** | Returning parsed scientific values directly to a model; unbounded retries |
| **FAILURE MODES** | Timeout, rate limit, auth failure, partial response, schema change |
| **FALLBACK** | Cache → snapshot → climatology, each stamping `degradation_state` |
| **TESTS** | `tests/contract/test_adapters_*.py` with recorded fixtures — **no live calls in CI** |
| **DONE** | Auth, timeout, retry w/ backoff, rate limit, validation, raw preservation, cache, version capture |

---

### `varuna_netra` — perception

| | |
|---|---|
| **INPUT** | SAR tiles (VV, VH) + ERA5 wind channel + `EvidenceEnvelope` |
| **OUTPUT** | `list[SlickDetection]` + envelope. Age is a **distribution** (`age_prior_mean_hours`, `age_prior_std_hours`) |
| **DEPENDS** | contracts, geospatial, data_guard |
| **LIBRARIES** | torch, segmentation-models-pytorch, torchgeo, rasterio, opencv, numpy |
| **FORBIDDEN** | Emitting a point age estimate; auto-escalating low confidence |
| **FAILURE MODES** | Look-alike FP, OOD scene, low-wind regime, land contamination |
| **FALLBACK** | Low confidence → route to human confirm. Wind < gate → flag `LOW_WIND`, downgrade. |
| **TESTS** | IoU/F1 on Zenodo test split; **look-alike FP rate reported separately**; OOD detection |
| **DONE** | Trained, exported, versioned in MLflow, model card written, FP rate published |

Architecture: `smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=3)`.
Loss `0.5·Dice + 0.5·CE`, inverse-frequency class weights. See `ML_TRAINING_GUIDE.md`.

---

### `varuna_prativartan` — reverse advection

| | |
|---|---|
| **INPUT** | `SlickDetection` (mask + age distribution), forcing ensemble |
| **OUTPUT** | `PhiField` — array + `PhiDiagnostics` + `SensitivityBlock` + envelope |
| **DEPENDS** | contracts, geospatial, data_guard, source_adapters |
| **LIBRARIES** | opendrift (OceanDrift), numpy, scipy, xarray, geopandas, shapely, pyproj |
| **FORBIDDEN** | `OpenOil` for backtracking (weathering is irreversible); silently truncating the ensemble |
| **FAILURE MODES** | Convergence collapse, multimodal field, boundary interaction, particle loss, runtime blowout |
| **FALLBACK** | Reduce M → set `REDUCED_ENSEMBLE` + widen uncertainty. Never silently proceed. |
| **TESTS** | `tests/scientific/` — seeded, known-answer synthetic fields; convergence regression |
| **DONE** | Φ normalises to 1.0, diagnostics populated, sensitivity computed, <2 min on demo HW |

**Φ `.npz` keys are locked:** `phi float32 (n_t,n_y,n_x) sum==1`, `lon_edges float64 (n_x+1,)`,
`lat_edges float64 (n_y+1,)`, `time_edges float64 (n_t+1,) unix`, `particle_count int32 (n_t,)`.
Assert `abs(phi.sum() - 1) < 1e-6` before writing.

Ensemble members must differ **structurally** (different forcing products), not only by
parameter jitter — jitter around one biased field keeps the ensemble centred on a wrong answer.

---

### `varuna_nyaya` — attribution

| | |
|---|---|
| **INPUT** | `PhiField`, `list[VesselTrack]`, optional `list[DarkVesselDetection]` |
| **OUTPUT** | `AttributionResultV2` + envelope |
| **DEPENDS** | contracts, geospatial, domain |
| **LIBRARIES** | numpy, scipy, scikit-learn, xgboost |
| **FORBIDDEN** | Importing prativartan/netra; naming a vessel when `distinguishability` is low; a constant latent term |
| **FAILURE MODES** | Flat posterior, two candidates in one Φ lobe, AIS gaps, miscalibration |
| **FALLBACK** | `NOT_DISTINGUISHABLE` or `INCONCLUSIVE` — both are correct outputs |
| **TESTS** | `tests/scientific/test_nyaya_*.py` — synthetic Φ with known answer; calibration ECE |
| **DONE** | Posterior sums to 1 with latent; ECE reported; ablation table produced |

```
L_k = Σ_i Φ[t_i, y_i, x_i] · Δt_i          (np.digitize per axis, vectorised)
L_k *= prior.combined * influence_weight
L_0 = 1 − Σ Φ[cells inside ANY track corridor]      ← NOT a constant
posterior = normalise({L_0, L_1..L_k})
top_gap   = p(1st) − p(2nd)
distinguishability ∈ [0,1]  — separation, NOT peakedness
entropy   = −Σ p log p / log(n)
```

`decision_state`: `STRONG_LEAD` · `WEAK_LEAD` · `NOT_DISTINGUISHABLE` · `LATENT_SOURCE` · `INCONCLUSIVE`.

---

### `varuna_chhaya` — latent investigation

| | |
|---|---|
| **INPUT** | SAR scene + AIS positions at scene time |
| **OUTPUT** | `list[DarkVesselDetection]` + `LatentFinding` |
| **DEPENDS** | contracts, geospatial |
| **LIBRARIES** | torch, xView3 reference model, numpy |
| **FORBIDDEN** | Concluding "dark vessel" from absence of AIS alone |
| **FAILURE MODES** | Scene footprint gaps, AIS latency, small-target misses |
| **FALLBACK** | `INSUFFICIENT_COVERAGE` when the footprint cannot support a conclusion |
| **TESTS** | Coverage-gap cases must return `INSUFFICIENT_COVERAGE`, never a dark claim |
| **DONE** | The four `LatentFinding` values are distinguished, each with a test |

---

### `varuna_pravaah` · `varuna_abhiyan` · `varuna_missions` · `varuna_alerts` · `varuna_praman` · `varuna_smriti`

| Module | Input → Output | Key rule |
|---|---|---|
| **pravaah** | slick + forcing → `ForwardForecast`, `LandfallPrediction` | Landfall is an **interval**, never a point time |
| **abhiyan** | case + assets → ranked `AssetTasking` | Feasibility filter first. No infeasible assignment. Exact optimisation at our scale. No RL. |
| **missions** | tasking + human approval → `MissionRecord` | `ASSIGNED` requires `human_approved_by`. FSM transitions validated. |
| **alerts** | event → delivery log | materiality → role router → content policy → freshness → channel adapter. Simulated providers must be labelled. |
| **praman** | case → `EvidenceManifest` | Raw refs + hashes + versions. Deterministic: same case ⇒ same manifest bytes. |
| **smriti** | outcomes → history, corridors, candidate datasets | **No online learning.** Human approval gate before any new model version. |

---

## 11. Testing

| Layer | Location | Rule |
|---|---|---|
| unit | `tests/unit/` | Pure logic, no I/O, fast |
| contract | `tests/contract/` | Schema + invariant compatibility. **Failing = architecture broken** |
| integration | `tests/integration/` | Needs postgres/redis/minio via compose |
| scientific | `tests/scientific/` | Seeded, known-answer, numerical regression with tolerances |
| robustness | `tests/robustness/` | Inject every failure in `FAILURE_THREAT_MATRIX.md`; assert degraded behaviour |
| e2e | `tests/e2e/` | Full pipeline on CASE-0001 |

```bash
make test              # unit + contract (fast, no services)
make test-integration  # requires docker compose up
make test-scientific   # seeded numerical regression
make test-all
```

Every P0/P1 row in the threat matrix must have a corresponding robustness test.

---

## 12. Honesty rules (hard constraints on output)

Never write, in code comments, docs, UI copy, or reports:

- that spill attribution is unsolved (Cerulean and CleanSeaNet ship it);
- that backward drift tracing is our innovation (the PS asks for it; Seatrack has done it ~20 years);
- that simulated evaluation validates operational performance;
- that Indian operational AIS is available (it is synthetic — label it);
- "patentable" (only "potentially patent-relevant");
- "real-time" (Sentinel-1 revisit is days — that constraint is *why* backward inference exists);
- "no Indian system exists" as fact (say "no publicly documented system");
- that the system determines guilt (it produces ranked leads for human sign-off).

Our contribution is the **probabilistic formulation**: ensemble uncertainty, origin
probability field, path-integral scoring, latent-source hypothesis, calibration,
distinguishability, and trust-aware operational decisioning.

---

## 13. Configuration · deployment · observability · security

- Config via `pydantic-settings` from `.env`. **Never hardcode secrets or paths.** `.env` is gitignored; `.env.example` is committed.
- `docker compose up` runs postgres+postgis, redis, minio, api, worker. See `DEPLOYMENT.md`.
- Structured logs (structlog → Loki), traces (OpenTelemetry), metrics (Prometheus → Grafana). Bind `case_id` on every log line in a case's path.
- JWT + RBAC; Argon2 password hashing; `bandit` and `pip-audit` in CI; Trivy on images.

---

## 14. Integration workflow

1. Branch from `develop`. One module or one vertical slice per branch.
2. Write the contract test first — it defines "done".
3. Implement. Keep `ruff` and `mypy` clean.
4. `make test` must pass locally before pushing.
5. **Integrate daily.** No branch stays unmerged for more than 24 hours.
6. Update `SETUP_STATUS.md` with the honest new status label.

---

## 15. WHEN THE LLM MUST STOP AND ASK A HUMAN

Stop and request review **only** when:

1. An **architectural change** is needed (module boundary, plane, dependency direction).
2. A **locked contract** in `varuna_contracts` would have to change.
3. **Scientific semantics** would change (what Φ means, what the posterior is over, how calibration is defined).
4. A **safety rule** would be violated (authorization gate, validity gate, no-online-training, human/AI separation).
5. **Real external credentials** or paid API access are required.
6. An **unsupported factual claim** would have to be written (see §12).
7. A **numerical or scientific result would have to be fabricated** — e.g. a benchmark number, an accuracy figure, or a calibration value that has not actually been computed.

**Otherwise: make a reasonable decision and proceed.** Record non-obvious choices in a
short ADR under `docs/adr/`. Do not block on style, naming, library minutiae, test
structure, or anything recoverable by a later edit.

---

## 16. Seven-day execution strategy

See `BUILD_PLAN_7_DAYS.md` for the full daily breakdown.

```
D1 foundation: contracts, repo, Docker, CI, Data Guard skeleton
D2 PRATIVARTAN + Φ + AIS ingest
D3 NYAYA + posterior + calibration + baselines
D4 NETRA + CHHAYA
D5 PRAVAAH + ABHIYAN + missions + PRAMAN
D6 PRAHARI + adapters + alerts + SMRITI
D7 integration + failure tests + deployment + rehearsal   ← no new features
```

Frontend works against mocks from day 1 and never blocks on backend.

---

## 17. Acceptance criteria — Definition of Done

A module is DONE only when **all** hold:

- [ ] implemented and fully type-hinted
- [ ] documented (module docstring states purpose, invariants, failure behaviour)
- [ ] unit + contract tests pass
- [ ] contract-compatible (imports only from `varuna_contracts`)
- [ ] structured logging with `case_id` bound
- [ ] failure behaviour defined and robustness-tested
- [ ] reproducible (seeded where stochastic)
- [ ] integrated on `develop`
- [ ] versioned (`processing_version` / `model_version` stamped on outputs)
- [ ] `SETUP_STATUS.md` updated with an honest status label

Scientific modules additionally:

- [ ] benchmarked against a baseline
- [ ] evaluated with uncertainty reported
- [ ] robustness-tested under degraded forcing
- [ ] limitations documented in the model card
