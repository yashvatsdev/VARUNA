<p align="center">
  <img src="https://img.shields.io/badge/SIH_2026-PS_SIH26143-blue?style=for-the-badge" alt="SIH 2026" />
  <img src="https://img.shields.io/badge/Organisation-NTRO-red?style=for-the-badge" alt="NTRO" />
  <img src="https://img.shields.io/badge/Theme-Space_Technology-purple?style=for-the-badge" alt="Space Technology" />
  <img src="https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-Proprietary-orange?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🌊 VARUNA GRID</h1>
<h3 align="center">National Marine Pollution Watch & Response Grid</h3>
<p align="center">
  <em>Oil Spill Detection · Probabilistic Vessel Attribution · Maritime Enforcement Intelligence</em>
</p>

<p align="center">
  <strong>Turns a drifting slick into a ranked, calibrated list of suspect vessels — or an evidence-backed statement that the culprit was running dark — and then warns the coast, tasks the aircraft, and builds the case.</strong>
</p>

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [What VARUNA Does](#-what-varuna-does)
- [Core Mechanism — RDPA](#-core-mechanism--rdpa)
- [System Architecture](#-system-architecture)
- [The Eight Subsystems](#-the-eight-subsystems)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Data Sources](#-data-sources)
- [Evaluation](#-evaluation)
- [Honesty Rules](#-honesty-rules)
- [Status](#-status)
- [Team](#-team)

---

## 🎯 The Problem

> **PS SIH26143** — *Leveraging satellite imagery to determine oil spills at sea along with AIS data correlations to identify the vessel responsible for the spill.*
>
> — **National Technical Research Organisation (NTRO)**, SIH 2026

Marine oil spills inflict enormous damage on ecosystems. Chronic operational discharges (illegal bilge dumping) vastly exceed headline tanker accidents in aggregate volume — and are **entirely deliberate**, therefore **deterrable**.

**The core challenge:** Oil is a drifting, deforming record of a crime whose timestamp and location have been erased by the ocean. By the time a satellite passes overhead — hours or days later — the slick has moved, the ship is a hundred nautical miles away, and every deployed tool tries to identify the culprit by looking at where the evidence *ended up* rather than reconstructing where it *began*.

### Why India, Why Now

| Factor | Detail |
|---|---|
| **Geography** | India sits astride the Gulf → Malacca tanker artery. ~7,500 km coastline. Dense traffic through the Gulf of Kutch, Mumbai High, and the Palk Bay approaches. |
| **Revisit Gap** | Sentinel-1 revisit over the Indian EEZ is a matter of days, not hours. **India's default case is the aged slick** — precisely where geometric matching fails. |
| **Institutional Gap** | ITOPF's country profile describes **no satellite attribution capability** and no vessel identification mechanisms. |

---

## 🔱 What VARUNA Does

> *"Today, a spill is detected and the file is closed as source unknown. VARUNA closes the loop: it names the ship, warns the coast, launches the aircraft, and builds the case — in the eleven minutes before the duty officer finishes his tea."*

VARUNA inserts the **missing inferential step** between "a slick exists" and "a human decides." It does not replace detection, and it does not replace the officer. It provides:

1. **Probabilistic origin reconstruction** — where and when the oil was released
2. **Calibrated vessel attribution** — ranked suspects with defensible confidence scores
3. **Dark vessel hypothesis testing** — explicit scoring of non-broadcasting culprits
4. **Impact forecasting** — where the slick will land, and when
5. **Response asset tasking** — which aircraft, which search box, which pattern
6. **Evidence packaging** — a checksummed, prosecutable case file
7. **Offender intelligence** — repeat-offender graphs and pollution corridor memory

---

## 🧪 Core Mechanism — RDPA

**Reverse-Drift Posterior Attribution** with a latent dark-vessel hypothesis.

Instead of asking *"which ship is lying alongside this slick?"*, VARUNA reconstructs **where and when the oil was released** as a probability field, then scores every candidate vessel by how much of that field its trajectory actually explains.

```
INPUT       Sentinel-1 SAR scene · slick mask · ERA5 wind · CMEMS currents · AIS tracks

STEP 1      SEGMENT slick → contour, area, elongation, AGE PRIOR (a distribution, not a point)

STEP 2      ENSEMBLE REVERSE ADVECTION — N particles × M perturbed forcing realisations
            → N×M backward trajectories, not one streamline

STEP 3      Build 4-D ORIGIN PROBABILITY FIELD Φ(x, y, t)

STEP 4      PATH-INTEGRAL LIKELIHOOD — for each AIS track k:
              L_k = ∫ Φ(x_k(t), y_k(t), t) dt
            weighted by emission prior π_k (vessel type, AIS gaps, behaviour)

STEP 5      LATENT-SOURCE HYPOTHESIS L₀ — residual Φ mass no observed track explains
            (high residual ⇒ a dark vessel was there)

STEP 6      NORMALISE → calibrated posterior over all candidates + latent source
            Or: INCONCLUSIVE (flat posterior — a first-class result, not an error)

OUTPUT      Ranked vessels with calibrated probabilities | "latent source dominant" | INCONCLUSIVE
```

### Why This Formulation

It is the only one that **degrades gracefully with slick age**: as the origin field widens, probabilities spread and the system says so — instead of confidently naming the nearest innocent ship.

---

## 🏗 System Architecture

```
PRAHARI(cut) → NETRA → PRATIVARTAN → NYAYA ←── CHHAYA
                 M2,M3      M5          M7-M10     xView3
                              ↓           ↓
                          PRAVAAH      ABHIYAN → PRAMAN → SMRITI
                            M11        greedy     M13      M12
```

Linear, auditable, no branching. In-process Python calls; REST only for the frontend.

### Operational Loop

```
[ PRAHARI ]      every Sentinel-1 pass over the EEZ
     ↓
[ NETRA ]        oil, or a look-alike?         → confidence, rejected FPs
     ↓
[ PRATIVARTAN ]  where did it come FROM?       → Φ(x,y,t) origin field
     ↓                                       ↘
[ NYAYA ]        who did it?                    [ CHHAYA ] …or who was hiding?
     ↓                                       ↙
[ PRAVAAH ]      where will it LAND, and when? → named coast + countdown
     ↓
[ ABHIYAN ]      what do we DO right now?      → asset + search box + ETA
     ↓
── HUMAN ──      duty officer approves / overrides / marks inconclusive
     ↓
[ SETU ]         ICG station · DG Shipping · State PCB · fishermen SMS
     ↓
── REALITY ──    overflight result · oil fingerprint · Oil Record Book audit
     ↓
[ PRAMAN ]       case file sealed, versioned, prosecutable
     ↓
[ SMRITI ]       outcome recalibrates NYAYA · offender graph grows
     ↓
     └──────── the system is now better than it was ────────┘
```

---

## 🧩 The Eight Subsystems

| # | Name | Function | Description |
|---|---|---|---|
| 01 | **PRAHARI** | Persistent EEZ Watch | Continuously ingests Sentinel-1 passes, tiles, detects, triages. *(Cut for hackathon — pre-ingest scenes)* |
| 02 | **NETRA** | Slick Detection & Look-alike Rejection | U-Net on VV+VH with ERA5 wind as an extra input channel. Outputs mask, class, confidence. |
| 03 | **PRATIVARTAN** ★ | Reverse-Drift Origin Engine | OpenDrift ensemble backwards under perturbed forcing → Φ(x,y,t). |
| 04 | **NYAYA** ★ | Attribution & Dark-Source Hypothesis | Path-integral scoring against Φ, weighted by behavioural priors, competed against the latent hypothesis. |
| 05 | **CHHAYA** | Dark Vessel Resolver | xView3 pretrained SAR ship detector, cross-referenced with AIS. |
| 06 | **PRAVAAH** | Impact & Landfall Forecast | Forward drift: projects 24–72h onto the coast. Which beach, which fishing ground, how many hours. |
| 07 | **ABHIYAN** ★ | Response Asset Tasking | Compute which asset, which search box, what pattern to maximise confirmation probability per hour flown. |
| 08 | **SMRITI** | Offender Intelligence & Hotspot Memory | Stores every case. Repeat-offender graph, pollution-corridor heatmap, watchlist. |

### Supporting Layers

| Name | Function |
|---|---|
| **PRAMAN** | Evidence pack — checksummed MARPOL Annex I case file: scene IDs, model versions, forcing versions, Φ snapshot, chain of custody. |
| **SETU** | Dissemination — routes alerts to ICG station, DG Shipping, State PCB, and multilingual SMS to fishermen. |

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| **Drift Physics** | OpenDrift / OpenOil (GPLv2) |
| **Machine Learning** | PyTorch + segmentation-models-pytorch |
| **Geospatial** | rasterio · xarray · GeoPandas · Shapely · pyproj |
| **SAR Preprocessing** | ESA SNAP / pyroSAR |
| **Backend** | FastAPI + Celery + Redis |
| **Database** | PostgreSQL + PostGIS |
| **Object Storage** | MinIO (S3-compatible) |
| **Frontend** | React + MapLibre GL + deck.gl |
| **Model Export** | TorchScript / ONNX Runtime |
| **Infrastructure** | Docker Compose |
| **Data Config** | Pydantic v2 + structlog |

---

## 📁 Project Structure

```
VARUNA/
├── README.md                       # ← You are here
├── VARUNA_MASTER_CONTEXT.md        # Complete project context & strategy document
├── CLAUDE.md                       # Quick reference for development sessions
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Full infrastructure stack
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git ignore rules
│
├── src/                            # Source code
│   ├── common/                     # Shared contracts & utilities
│   │   ├── schemas.py              # THE contract — all subsystem data types
│   │   ├── config.py               # Centralised configuration
│   │   ├── geo_utils.py            # Geospatial helpers
│   │   └── logging.py              # Structured logging setup
│   │
│   ├── netra/                      # M2/M3: Slick detection & characterisation
│   ├── prativartan/                # M5: Reverse-drift origin engine (Φ field)
│   ├── nyaya/                      # M7-M10: Attribution & dark-source hypothesis
│   ├── chhaya/                     # M9b: Dark vessel resolver (xView3)
│   ├── pravaah/                    # M11: Forward drift & landfall forecast
│   ├── ais/                        # M6: AIS ingest & track builder
│   ├── abhiyan/                    # Response asset tasking
│   ├── smriti/                     # Offender intelligence & memory
│   ├── praman/                     # Evidence manifest & case files
│   ├── eval/                       # Simulation harness & evaluation
│   └── api/                        # FastAPI application & routes
│       └── routes/
│
├── experiments/                    # Experimental validation
│   └── go_nogo/                    # Week-1 discriminability harness
│       ├── core.py
│       ├── run.py
│       ├── sweep.py
│       └── visualize.py
│
├── data/                           # Data directory (gitignored)
│   ├── cache/
│   ├── forcing/                    # CMEMS currents, ERA5 wind (NetCDF)
│   └── scenes/                     # SAR imagery
│
├── models/                         # Trained model weights (gitignored)
│
├── tasks/                          # Per-person work assignments
│   ├── P1_ARCHITECT.md
│   ├── P2_ML_VISION.md
│   ├── P3_PHYSICS.md
│   ├── P4_BACKEND.md
│   ├── P5_FRONTEND.md
│   └── P6_PRODUCT.md
│
└── docs/                           # Design documentation
    └── DECISIONS.md                # Architecture decision records
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Conda (recommended for OpenDrift)

### 1. Clone the Repository

```bash
git clone https://github.com/Soumya080/VARUNA.git
cd VARUNA
```

### 2. Environment Setup

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials (Copernicus, CDS API, etc.)
```

### 3. Install Dependencies

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# OpenDrift may require conda:
# conda install -c opendrift -c conda-forge opendrift
```

### 4. Start Infrastructure

```bash
# Launch PostgreSQL+PostGIS, Redis, MinIO
docker-compose up -d postgres redis minio
```

### 5. Run the API

```bash
# Development server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Or via Docker Compose (full stack)
docker-compose up
```

---

## 📊 Data Sources

| Source | Type | Access |
|---|---|---|
| [Zenodo Sentinel-1 Oil Spill Dataset](https://zenodo.org/records/8346860) | SAR imagery + masks (1,200 images) | Open — CC-BY-4.0 |
| [Eastern Mediterranean Slicks + Look-alikes (ESSD 2025)](https://essd.copernicus.org/articles/17/6807/2025/) | 3,225 oil + 2,290 look-alike patches | Open — CC-BY-4.0 |
| [MarineCadastre AIS](https://marinecadastre.gov/accessais/) | Vessel traffic (US waters) | Open |
| [Sentinel-1 GRD](https://dataspace.copernicus.eu/) | Raw SAR scenes (global) | Free registration |
| [CMEMS Ocean Currents](https://data.marine.copernicus.eu/) | Surface current fields | Free registration |
| [ERA5 Wind](https://cds.climate.copernicus.eu/) | 10m wind components | Free registration |
| [xView3-SAR](https://github.com/allenai/sar_vessel_detect) | Dark vessel detection model | Open |

---

## 📈 Evaluation

### North-Star KPI

> **Top-1 attribution accuracy at 24-hour slick age with ≥20 vessels in the envelope, subject to ECE < 0.05.**

### Evaluation Axes

| Axis | What It Measures |
|---|---|
| **Attribution vs. Slick Age** | Top-1/Top-3 accuracy at 2, 6, 12, 24, 48h |
| **Attribution vs. Traffic Density** | Accuracy at 5, 20, 50, 100+ vessels |
| **Calibration** | Expected Calibration Error (ECE) + reliability diagrams |
| **Latent-Source Detection** | Precision/recall on "was this a dark vessel?" |
| **Perception** | IoU/F1 on segmentation; FP rate on look-alike set |
| **Ablations** | ensemble vs. single trajectory · path-integral vs. nearest-point · ± emission prior · ± latent term |

### Baselines

1. Nearest vessel to slick (naïve)
2. Cerulean-style geometric matching (parity / proximity / temporality)
3. Single deterministic backtrack (Seatrack-style)

---

## ⚖️ Honesty Rules

These are **non-negotiable**. They come from [Section 18 of the master context](VARUNA_MASTER_CONTEXT.md):

- ❌ Attribution is **not** unsolved — Cerulean and CleanSeaNet ship it
- ❌ Backward drift is **not** our innovation — the PS asks for it; Seatrack has done it for 20 years
- ✅ **Ours is the probabilistic formulation:** ensemble uncertainty, path integral, latent term, calibration
- ⚠️ Simulated evaluation ≠ operational validation
- ⚠️ Indian AIS is synthetic — **say so on the slide**
- ❌ Never "patentable", never "real-time", never "no Indian system exists"
- ✅ The system **never** names a ship without human sign-off
- ✅ `INCONCLUSIVE` is a valid, first-class output

---

## 📌 Status

> **23 August 2026** — Design complete. Bootstrap complete (schemas, config, skeleton, task files). No subsystem code yet.

- **Go/no-go experiment:** NOT YET ESTABLISHED. Initial harness returned 100% top-1, but the harness cannot fail (see [`docs/DECISIONS.md`](docs/DECISIONS.md) §1 for a full defect list). Fair rebuild shows ~12% top-1 — above chance (5%), indicating signal exists. Harness is being rebuilt properly.
- **Architecture:** Locked. Eight subsystems, linear pipeline, in-process calls.
- **Schemas:** Complete. All cross-subsystem data contracts defined in [`src/common/schemas.py`](src/common/schemas.py).
- **Task files:** All six team member assignments ready in [`tasks/`](tasks/).

---

## 👥 Team

Six-person team for SIH 2026. Work is organised across six parallel tracks with zero cross-dependency until day 4:

| Track | Scope | Details |
|---|---|---|
| **P1 — Architect** | Go/no-go rebuild, NYAYA, eval harness | [`tasks/P1_ARCHITECT.md`](tasks/P1_ARCHITECT.md) |
| **P2 — ML/Vision** | NETRA training (GPU), CHHAYA setup | [`tasks/P2_ML_VISION.md`](tasks/P2_ML_VISION.md) |
| **P3 — Physics** | OpenDrift engine, forcing cache | [`tasks/P3_PHYSICS.md`](tasks/P3_PHYSICS.md) |
| **P4 — Backend** | API, AIS, PostGIS, SMRITI | [`tasks/P4_BACKEND.md`](tasks/P4_BACKEND.md) |
| **P5 — Frontend** | Console on mock Φ | [`tasks/P5_FRONTEND.md`](tasks/P5_FRONTEND.md) |
| **P6 — Product** | Demo cases, slides, video, rehearsal | [`tasks/P6_PRODUCT.md`](tasks/P6_PRODUCT.md) |

---

## 🔗 Key Interfaces

| Interface | Flow | Description |
|---|---|---|
| `SlickDetection` | NETRA → PRATIVARTAN | Carries an age **distribution**, not a point estimate |
| `PhiFieldMeta` + `.npz` | PRATIVARTAN → NYAYA/frontend | 3-D histogram (n_t, n_y, n_x), normalised to sum=1 |
| `VesselTrack` | AIS → NYAYA | `transponder_active=False` drives judge control |
| `AttributionResult` | NYAYA → everything | Posteriors sum to 1 **with** `latent_source` |

---

## 📄 Conventions

- **Python 3.10+**, full type hints, Pydantic v2, structlog
- **UTC tz-aware** datetimes only — never naive
- **WGS84** (lon, lat) ordering
- **km / km² / knots** for all measurements
- **Absolute imports** from `src.`
- Model + forcing versions recorded on every artefact

---

<p align="center">
  <em>Named for the Vedic god of the ocean and of ṛta (cosmic law) — the deity who binds those who break it.</em>
</p>
