# CHANGELOG

Format: [Keep a Changelog](https://keepachangelog.com/1.1.0/) · [Semantic Versioning](https://semver.org/)

---

## [2.0.0] — 2026-08-24

Restructure to the **trust-aware, fail-safe v2 architecture**. Team moves from six roles to
four. Contract package is now the locked source of truth.

### Added — contracts (VERIFIED, 22 passing tests)

- `varuna_contracts.evidence` — `EvidenceEnvelope` on every subsystem output, with
  provenance, trust, quality, uncertainty, calibration/validity/degradation state, anomaly
  flags, content hashing. `derive()` enforces **monotonic degradation**.
- **Bounded Evidence Influence** — `influence_weight ∈ [0,1]` capped by trust state.
  Suspicious data is down-weighted, never mutated. Explicitly *not* PPO clipping (ADR-0003).
- `varuna_contracts.states` — case state as **four independent axes** (investigation,
  outcome, response, evidence) + lifecycle; `check_case_invariants()`; mission FSM with a
  hard authorization gate (`ASSIGNED` requires `human_approved_by`).
- `varuna_contracts.phi` — Φ as a **structured object**: time distribution, spatial modes,
  `PhiDiagnostics` (convergence, entropy, effective support, multimodality, particle loss),
  and `SensitivityBlock` (age / forcing / diffusivity / weathering → `dominant_assumption`).
- `varuna_contracts.decision` — `AttributionResultV2` separating **belief from
  distinguishability**; `DecisionState` incl. `NOT_DISTINGUISHABLE`; `LatentFinding`
  distinguishing *no visible source* from *insufficient coverage*; `ValidityGateResult` as
  a mandatory pre-action checkpoint.

### Added — documentation

`ARCHITECTURE_V2.md` (three planes, trust boundaries, Mermaid sequence/state/deployment
diagrams) · `FAILURE_THREAT_MATRIX.md` (47 threats: 27 P0, 20 P1, each with containment and
a required test) · `LLM_IMPLEMENTATION_GUIDE.md` (universal context packet, per-module
contracts, "when the LLM must stop") · `ML_TRAINING_GUIDE.md` · `COMPUTE_SPEC.md` ·
`BUILD_PLAN_7_DAYS.md` · `DEPLOYMENT.md` · `SECURITY.md` · `DATA_CATALOG.md` ·
`EVALUATION.md` · `CONTRIBUTING.md` · `SETUP_STATUS.md` · ADR-0001/0002/0003.

### Added — infrastructure

- `infra/docker/Dockerfile` and `Dockerfile.physics` (OpenDrift via micromamba, separate image)
- `pyproject.toml` (Python 3.12, `packages/` source root), `Makefile`, GitHub Actions CI
  with lint, types, contract tests, security scanning, and image build

### Changed

- **Repository restructured** `src/` → `packages/varuna_*` + `apps/` (ADR-0001)
- **`docker-compose.yml` fixed** — previously referenced `build: .` with **no Dockerfile**,
  so the stack could never start
- **Team model** six roles → four (`tasks/ROLE_01..04`)
- Python 3.10 → **3.12**
- README rewritten with honest status labels throughout

### Removed

- `tasks/P1..P6` (six-person model)

### Fixed — documentation honesty

Removed unverified "bootstrap complete" / "schemas complete" framing. Status now traces to
repository evidence via `SETUP_STATUS.md`.

### ⚠️ Known invalid

**`experiments/go_nogo/` is invalid and its 100% top-1 result must not be quoted.** The
harness cannot fail: innocent vessels sit a median 33 km from the origin, the guilty track
ends 18 h before observation so the baseline can never win, `L₀` is fixed at `1/(2N+1)`,
the backward ensemble is centred on the exact truth field, and the true slick age is passed
in. Rebuilt fairly → **~12% top-1** (chance 5%). See `EVALUATION.md` §0 and
`FAILURE_THREAT_MATRIX.md` §8. Calibration is blocked until the rebuild passes the validity
checklist.

---

## [1.0.0] — 2026-08-23

Initial bootstrap: v1 linear pipeline, Pydantic contracts in `src/common/schemas.py`,
six-person task files, go/no-go experiment harness, project documentation.
