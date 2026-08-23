# COMPUTE_SPEC.md
## VARUNA GRID v2 — hardware plan

> **All performance figures below are ESTIMATES** derived from component specifications and
> typical throughput for comparable workloads. **None have been measured on this codebase**
> — nothing has been run yet (see `SETUP_STATUS.md`). Replace each estimate with a measured
> value as soon as the corresponding module runs, and mark it MEASURED.

---

## 1. Workload profile

| Workload | Bound by | GPU? | Parallel |
|---|---|---|---|
| NETRA training | GPU compute + VRAM | **Yes** | Single GPU sufficient |
| NETRA inference | GPU (or CPU, slower) | Optional | Batch over tiles |
| CHHAYA (xView3) | GPU for speed | Optional | Batch over tiles |
| **PRATIVARTAN ensemble** | **CPU cores + RAM** | No | **Embarrassingly parallel over members** |
| PRAVAAH forward drift | CPU | No | Same |
| NYAYA path integral | CPU, pure NumPy | No | Vectorised, milliseconds |
| Calibration sweep | CPU | No | Embarrassingly parallel over trials |
| API / DB / MinIO | I/O | No | — |

**The key sizing insight:** the scientifically distinctive part of this system — the
backward ensemble — is **CPU-bound, not GPU-bound**. Core count matters more than the GPU
for everything except training. A machine with a modest GPU and 16 cores will outperform
one with a strong GPU and 4 cores on the actual demo path.

---

## 2. Configurations

### MINIMUM — one developer, will work but slowly

| Component | Spec | Consequence |
|---|---|---|
| CPU | 4 cores / 8 threads | Φ ensemble ~4× slower than recommended |
| RAM | 16 GB | Reduce `PHI_N_PARTICLES`; watch swap |
| GPU | None (or 6 GB, e.g. GTX 1660 Ti) | Train at 256² tiles, batch 4; or use Colab |
| Storage | 256 GB SSD | Cannot hold all of Zenodo I–III + forcing |
| OS | Linux / WSL2 / macOS | Windows-native GDAL is painful — use WSL2 or Docker |

*Estimated:* Φ (N=2000, M=20, 24 h) ≈ **6–10 min**. NETRA training on Colab, not locally.

### RECOMMENDED — the team's working target

| Component | Spec | Rationale |
|---|---|---|
| CPU | **8–16 cores** (Ryzen 7/9, i7/i9) | Ensemble members run one per core |
| RAM | **32 GB** | Φ arrays + xarray forcing + PostGIS |
| GPU | **NVIDIA 12–16 GB** (RTX 3060 12 GB, 4070, T4, A10) | NETRA at 512², batch 8, AMP |
| Storage | **1 TB NVMe** | Zenodo ~45 GB + ESSD ~5 GB + forcing ~15 GB + scenes + Φ |
| Network | Broadband | 45 GB initial pull |

*Estimated:* Φ (N=2000, M=50, 24 h) ≈ **90–150 s** on 8 cores — meets the <2 min budget.
NETRA training ≈ **4–8 h**. Calibration sweep (500 cases) ≈ **3–6 h**, run overnight.

### IDEAL — comfortable, not required

| Component | Spec |
|---|---|
| CPU | 24–32 cores (Threadripper / Xeon) |
| RAM | 64–128 GB |
| GPU | RTX 4090 24 GB or A100 40 GB |
| Storage | 2 TB NVMe + NAS for archives |

*Estimated:* Φ ≈ **25–40 s**. NETRA training ≈ 1.5–3 h. Full 3,000-trial sweep ≈ 1–2 h.

---

## 3. Per-component detail

### NETRA training

| Tile | Batch | VRAM (est.) | Note |
|---|---|---|---|
| 256² | 8 | ~4 GB | Fits 6 GB cards |
| 512² | 8 | ~10 GB | **Recommended** |
| 512² | 16 | ~18 GB | Needs 24 GB |

AMP roughly halves activation memory and gives ~1.5–2× throughput. Gradient accumulation
substitutes for batch size on small cards. Cloud fallback: Colab Pro (~$12/mo, T4/A100) or
Kaggle (30 GPU-hours/week, P100) — checkpoint to Drive every epoch.

### PRATIVARTAN — the sizing that matters

Cost scales as `N × M × (T/dt)`.

| N (particles) | M (members) | Duration | Cores | Est. wall time |
|---|---|---|---|---|
| 500 | 20 | 24 h | 4 | ~45 s |
| 2000 | 50 | 24 h | 8 | **~2 min** ← demo target |
| 2000 | 50 | 48 h | 8 | ~4 min |
| 5000 | 100 | 48 h | 16 | ~8 min |

Memory ≈ `N × M × steps × 2 coords × 8 bytes`. At N=2000, M=50, 96 steps ≈ **150 MB** of
trajectories, plus the forcing arrays held by xarray (usually the larger term).

**Under compute pressure: reduce M, set `degradation_state=REDUCED_ENSEMBLE`, and widen the
reported uncertainty. Never silently truncate** (threat P-06).

Parallelise with `multiprocessing.Pool` over ensemble members — each is fully independent.

### Backend services

| Service | RAM | Disk | Note |
|---|---|---|---|
| PostgreSQL + PostGIS | 2–4 GB | 20–50 GB | AIS points dominate; index `(mmsi, timestamp)` |
| Redis | 512 MB – 1 GB | 1 GB | Queue + cache |
| MinIO | 512 MB | **500 GB+** | Scenes, Φ fields, raw evidence (never deleted) |
| FastAPI | 512 MB/worker | — | 2–4 workers |
| Celery default | 1–2 GB/worker | — | I/O-bound tasks |
| Celery physics | **2–4 GB/worker** | — | One worker, high concurrency |
| MLflow | 512 MB | 10 GB | Artifacts |
| Monitoring | 2 GB total | 20 GB | Prometheus + Grafana + Loki retention |

**Estimated total for the full stack: ~12 GB RAM.** With 32 GB, that leaves comfortable
headroom for a Φ ensemble running alongside.

---

## 4. Storage budget

| Item | Size | Growth |
|---|---|---|
| Zenodo I–III | ~45 GB | Fixed |
| ESSD look-alikes | ~5 GB | Fixed |
| MarineCadastre AIS (1 month, GoM) | ~2 GB CSV | ~2 GB/month |
| CMEMS currents (3 regions × 1 month) | ~5–15 GB | Per region-month |
| ERA5 wind (same) | ~2–5 GB | Per region-month |
| SAR demo scenes | ~5 GB | ~1 GB/scene |
| Φ fields | ~50–200 MB each | **Per case — never deleted (PRAMAN)** |
| Model checkpoints | ~5 GB | Per experiment |
| **Total working set** | **~80–100 GB** | 1 TB gives real headroom |

Raw evidence is append-only and never deleted. Plan MinIO growth accordingly.

---

## 5. Demo-day hardware

| | |
|---|---|
| **Primary** | Recommended laptop — 8+ cores, 32 GB, 12 GB GPU, 1 TB NVMe |
| **Everything cached** | Model weights, forcing NetCDF, SAR scenes, pre-computed Φ, basemap MBTiles |
| **`DEMO_MODE=true`** | Serves frozen artifacts, **zero external calls** |
| **Backup 1** | Second machine with the same SSD restore — **tested, not assumed** |
| **Backup 2** | Replay mode from a recorded SSE session |
| **Backup 3** | Recorded video |

Air-gapped by design: nothing on the demo path requires network.

---

## 6. Cost

| Item | Cost |
|---|---|
| Colab Pro (1–2 months, if no local GPU) | ~$12–24 |
| Kaggle GPU (30 h/week) | Free |
| All datasets (Zenodo, ESSD, CMEMS, ERA5, MarineCadastre, xView3) | Free |
| All software | Free / open source |
| **Total additional spend** | **≈ $0–50** |

Deployment target claim: a single GPU workstation, all-open-source, air-gappable, running
on hardware a coastal agency already owns.

---

## 7. Failure modes and fallbacks

| Failure | Fallback |
|---|---|
| GPU OOM in training | Reduce tile to 256², batch to 4, enable gradient accumulation |
| GPU unavailable at demo | Cached NETRA outputs; CPU inference (~5 s/tile) |
| Φ exceeds time budget | Reduce M → `REDUCED_ENSEMBLE` + widened uncertainty, surfaced in UI |
| RAM exhaustion in ensemble | Chunk members; stream trajectories to disk |
| Disk full | Φ fields are the growth term — archive old cases, never delete raw evidence |
| Forcing download too slow | Pre-cache before travel; climatology fallback stamps degradation |

---

## 8. Scaling beyond the prototype

Current design is single-node Docker Compose, deliberately. The realistic scaling path:

1. **Separate the physics worker** onto a high-core machine (already a distinct image and queue).
2. **Add Celery workers horizontally** — the queue already supports it.
3. **PostGIS read replica** for analytics if SMRITI queries start competing with the API.
4. **Object storage to real S3** — MinIO speaks the same API, so this is configuration.

Kubernetes is not on this path at four people and single-node scale. Reintroducing it
requires an ADR that addresses that specific point.
