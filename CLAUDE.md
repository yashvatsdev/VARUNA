# CLAUDE.md — VARUNA GRID v2

Oil spill detection + probabilistic vessel attribution, SIH 2026 PS SIH26143 (NTRO).
Trust-aware, fail-safe architecture. Four-person team.

## Source of truth (higher wins)

1. `packages/varuna_contracts/` (code) → 2. `docs/adr/` → 3. `ARCHITECTURE_V2.md` →
4. `FAILURE_THREAT_MATRIX.md` → 5. `LLM_IMPLEMENTATION_GUIDE.md` → 6. `tasks/ROLE_*.md` →
7. README/this file. `SETUP_STATUS.md` is the authority on **what is implemented**.
`VARUNA_MASTER_CONTEXT.md` is v1-era domain background — its architecture is superseded.

**The repository is the authority.** Never infer something exists because a doc says "complete".

## Current status (24 Aug 2026)

- ✅ **Contracts VERIFIED** — 22 passing contract tests (`tests/contract/`)
- ⚠️ **Go/no-go NOT ESTABLISHED** — `experiments/go_nogo/` is invalid; its 100% cannot be
  quoted. Fair rebuild → ~12% (chance 5%). See `docs/DECISIONS.md` §1.
- ❌ **Scientific pipeline not implemented** — all modules scaffolded
- ❌ Stack never started; Docker never built; OpenDrift not installed; Python is 3.10 locally (spec: 3.12)
- ❌ P0 threat coverage: 4 / 27

## Architecture in one line

`External → Adapter → Ingestion Gate → DATA GUARD → Flow Inspection → NETRA →
PRATIVARTAN → Φ+diagnostics → NYAYA ← CHHAYA → ★VALIDITY GATE★ → PRAVAAH →
ABHIYAN → Mission FSM → ★AUTHORIZATION★ → HUMAN → Action Gateway → SMRITI`

Three planes: **data** (moves cases) · **control** (decides what's allowed) ·
**governance** (records what happened). The two ★ gates are mandatory chokepoints.

## Architectural invariants (enforced by tests)

1. Fail safely, not silently — no swallowed exceptions, no silent defaults
2. Raw evidence never overwritten
3. **Trust ≠ confidence** — source vs measurement, never collapsed
4. Uncertainty propagates — always use `EvidenceEnvelope.derive()`
5. Every boundary output carries an envelope
6. No external HTTP outside `varuna_source_adapters`
7. No action without `human_approved_by`
8. `INCONCLUSIVE` / `NOT_DISTINGUISHABLE` are valid outcomes
9. Human decisions and AI recommendations stored separately
10. **Bounded Evidence Influence** — down-weight via `influence_weight`, never mutate values (not PPO)
11. SMRITI never self-trains online — human approval gate required
12. Honesty rules are hard constraints on output

## Conventions

Python 3.12 · full type hints · Pydantic v2 at boundaries · structlog (bind `case_id`) ·
UTC tz-aware only · WGS84 (lon, lat) · km/km²/knots · absolute imports
(`from varuna_contracts import ...`) · line 100 · ruff + mypy clean · seed all randomness.

## Commands

```bash
pip install -e ".[dev]"                              # install
PYTHONPATH=packages python -m pytest tests/contract -q  # 22 passed (works today)
make test          # unit + contract, no services
make up-infra      # postgres + redis + minio
make check         # lint + typecheck + test (CI gate)
make demo          # DEMO_MODE=true, frozen artifacts, zero external calls
```

## Role ownership

| Role | Owns | File |
|---|---|---|
| 01 Scientific/ML | NETRA · PRATIVARTAN · NYAYA · CHHAYA · calibration | `tasks/ROLE_01_SCIENTIFIC_ML.md` |
| 02 Data/Backend | Data Guard · adapters · AIS · PostGIS · API · Event Spine · PRAMAN | `tasks/ROLE_02_DATA_BACKEND.md` |
| 03 Frontend/Geo | Cockpit · map · missions UI · field mode · alerts | `tasks/ROLE_03_FRONTEND_GEO.md` |
| 04 MLOps/Ops | PRAVAAH · ABHIYAN · missions · alerts · Docker · CI · SMRITI pipeline | `tasks/ROLE_04_MLOPS_OPS.md` |

## Do NOT

Redefine contract types · call external APIs outside adapters · mutate suspicious values
(down-weight instead) · return bare floats/dicts across boundaries · `except: return 0.0` ·
let an LLM compute Φ/posteriors/trust/assignments/severity · add Kafka/K8s/vector DB/RAG/
agents/RL-in-core · online self-training · write a number that didn't come from the
pipeline · mark work "complete" without a passing test.

## Honesty rules

Attribution is **not** unsolved (Cerulean, CleanSeaNet ship it). Backward drift is **not**
our innovation (PS asks for it; Seatrack ~20 years). Ours is the *probabilistic
formulation*: ensemble uncertainty, path integral, latent term, calibration,
distinguishability, trust-aware decisioning. Simulated ≠ operational validation. Indian AIS
is synthetic — say so. Never "patentable" / "real-time" / "no Indian system exists".
Never name a ship without human sign-off.

## Current P0 risks

1. **Go/no-go invalid** — every downstream claim depends on rebuilding it honestly (ROLE 01)
2. **Nothing runs** — no Dockerfile build, no OpenDrift (ROLE 04, day 1, blocks ROLE 01)
3. **23 of 27 P0 threats untested**
4. Calibration blocked until the harness is valid (threat N-06)

## ADRs

Architecture/contract/scientific-semantics changes need an ADR in `docs/adr/`
(`ADR-NNNN-short-title.md`: context · decision · consequences · rejected alternatives).
Otherwise decide and proceed — record non-obvious choices briefly.

## Provenance

Every artifact: `artifact_id`, `parent_artifact_ids`, `produced_by`, `model_version`,
`processing_version`, `provenance.raw_artifact_refs`, `content_hash`. Build downstream
envelopes with `.derive()` — hand-construction that upgrades trust is a review blocker.

## Stop and ask a human when

architecture changes · a locked contract breaks · scientific semantics change · a safety
rule would be violated · real credentials are needed · an unsupported factual claim is
required · **a numerical/scientific result would have to be fabricated**. Otherwise
proceed independently.
