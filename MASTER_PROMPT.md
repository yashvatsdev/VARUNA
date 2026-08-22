# VARUNA GRID — The One Prompt
## Give this to Claude Code. It reads the master context and builds everything.

---

## COPY EVERYTHING BELOW THIS LINE INTO CLAUDE CODE

```
You are the technical co-founder and lead systems architect for VARUNA GRID — an oil spill detection + vessel attribution system for Smart India Hackathon 2026 (Problem Statement SIH26143, NTRO).

We are a 6-person team. Design is complete. Implementation starts NOW. You will bootstrap the entire production codebase.

═══════════════════════════════════════════════════════════════
PHASE 1: ABSORB (do silently — no summaries, no commentary)
═══════════════════════════════════════════════════════════════

Read this file completely — it is the ONLY source of truth:
  d:\SIH-26\VARUNA_MASTER_CONTEXT.md

Pay special attention to:
- Section 8: The core mechanism (ensemble reverse advection → Φ → path integral → posterior)
- Section 9: The 8 subsystems (PRAHARI through SMRITI)
- Section 10: System architecture + module table (M1-M15)
- Section 11: ML vs non-ML decisions (critical — what is ML and what is NOT)
- Section 13: Evaluation plan + north-star KPI
- Section 14: Tech stack (LOCKED — do not change)
- Section 16: Build plan + cut order
- Section 18: Honesty rules (NON-NEGOTIABLE)

Also note: We already ran the go/no-go discriminability experiment in d:\SIH-26\experiments\go_nogo\. Result: GO ✅ — 100% top-1 accuracy at 24h/20 vessels on synthetic currents. The core mechanism is validated.

═══════════════════════════════════════════════════════════════
PHASE 2: ARCHITECT (think, then write)
═══════════════════════════════════════════════════════════════

Before creating any files, think through these architectural decisions and document your reasoning in CLAUDE.md:

1. SUBSYSTEM PRIORITY FOR 7 DAYS:
   - The master context has 8 subsystems + 2 support layers + 15 modules
   - We have 6 people and 7 days. What is CORE vs IMPORTANT vs CUT?
   - The cut order is in Section 16.5 — follow it
   - PRAHARI (EEZ watch scheduler) is NOT needed for demo — we pre-load scenes
   - ABHIYAN can be greedy-nearest-asset, not a full optimizer
   - SETU can be a mock SMS panel
   - What's the MINIMUM set that makes all 6 demo moments work?

2. INTEGRATION ARCHITECTURE:
   - How do subsystems communicate? Direct function calls? Message queue? REST API?
   - For a hackathon: keep it simple. In-process Python calls for the pipeline, REST API only for frontend-backend communication
   - The pipeline is LINEAR: detect → backtrack → score → forecast. No branching, no agents.

3. PHI FIELD FORMAT:
   - KDE is slow and leaks memory. Use 3D numpy histogram instead.
   - Define the exact .npz format (arrays, shapes, dtypes)
   - This is the MOST CRITICAL interface — PRATIVARTAN produces it, NYAYA consumes it, Frontend renders it

4. WHAT CAN BE PARALLELIZED:
   - Training NETRA (GPU) has ZERO dependencies on anything else
   - OpenDrift engine setup has ZERO dependencies
   - AIS pipeline has ZERO dependencies
   - Frontend can use mock data until Day 4
   - Identify ALL parallel tracks

5. HACKATHON-SPECIFIC OPTIMIZATIONS:
   - Every demo case should have a PRE-COMPUTED fallback (cached Φ, cached posterior)
   - A recorded backup video of the full demo
   - All forcing data (CMEMS, ERA5) must be cached as local NetCDF BEFORE the event
   - Never depend on a live API during demo

═══════════════════════════════════════════════════════════════
PHASE 3: CREATE THE PROJECT (in this exact order)
═══════════════════════════════════════════════════════════════

Create these files and directories:

--- FILE 1: d:\SIH-26\CLAUDE.md ---
Project memory file. Must contain:
- One-sentence project description
- Architecture diagram (ASCII)
- Tech stack (from Section 14 of master context — do not change)
- Directory structure (the one you're about to create)
- Shared data schemas summary (what types flow between subsystems)
- Coding conventions (Python 3.10+, type hints, Pydantic v2, structlog, UTC everywhere, WGS84 lon-lat)
- Go/no-go status: GO ✅ (quick test passed 23 Aug 2026)
- What's done vs what's in progress
- Honesty rules from Section 18 (abbreviated)
- Token optimization rules for future LLM sessions:
  * Read CLAUDE.md once at session start
  * One subsystem per session
  * Reference build spec by section number
  * Write code directly, don't explain first
  * Use schemas.py for all shared types

--- FILE 2: d:\SIH-26\requirements.txt ---
All Python dependencies. Pin major versions. Include:
torch, torchvision, segmentation-models-pytorch, opendrift,
fastapi, uvicorn, celery, redis,
sqlalchemy, geoalchemy2, psycopg2-binary, alembic,
rasterio, xarray, netcdf4, geopandas, shapely, pyproj,
pydantic>=2.0, pydantic-settings,
structlog, python-dotenv, minio,
scipy, numpy, pandas, matplotlib, tqdm,
scikit-learn, onnxruntime,
pytest, httpx

--- FILE 3: d:\SIH-26\.env.example ---
All environment variables needed:
DATABASE_URL, REDIS_URL, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY,
MODEL_DIR, DATA_DIR, FORCING_DIR, OUTPUT_DIR,
NETRA_MODEL_PATH, CHHAYA_MODEL_PATH,
PHI_N_PARTICLES, PHI_N_ENSEMBLE, PHI_DT_SECONDS,
API_HOST, API_PORT, LOG_LEVEL

--- FILE 4: d:\SIH-26\src\common\schemas.py ---
THIS IS THE MOST IMPORTANT FILE. It defines ALL inter-subsystem data contracts.
Use Pydantic v2 BaseModel. Include:
- Enums: SlickClass, VerdictType, ForcingErrorLevel
- Geometry: BBox
- NETRA output: SlickDetection (with slick_id, classification, confidence, mask_path, centroid, area, elongation, age_prior_mean/std, observation_time, scene_id)
- AIS: AISPoint, VesselTrack (with gap metadata)
- PRATIVARTAN output: PhiFieldMeta (with phi_id, slick_id, n_particles, n_ensemble, backward_duration, time_bins, data_path, bbox)
- NYAYA output: VesselScore, LatentSourceScore, AttributionResult (with case_id, verdict, vessel_scores sorted by posterior, latent_source, ece)
- PRAVAAH output: LandfallPrediction, ForwardForecast
- Top-level: Case (combines detection + attribution + forecast)
Make these production-grade. Other subsystems will IMPORT from this file.

--- FILE 5: d:\SIH-26\src\common\config.py ---
Pydantic Settings class loading from .env. All paths, URLs, model parameters.

--- FILE 6: d:\SIH-26\src\common\geo_utils.py ---
Coordinate utilities: haversine distance, bbox expansion, point-in-polygon, lon-lat to meters.

--- FILE 7: d:\SIH-26\src\common\logging.py ---
Structured JSON logging via structlog. One setup function.

--- FILES 8+: Empty __init__.py for all subsystem packages ---
src/netra/, src/prativartan/, src/nyaya/, src/chhaya/, src/pravaah/, src/ais/, src/smriti/, src/abhiyan/, src/api/, src/api/routes/

--- FILE: d:\SIH-26\docker-compose.yml ---
Services: postgres (postgis/postgis:16-3.4), redis, minio, api (FastAPI on port 8000).
Volumes for data persistence.

═══════════════════════════════════════════════════════════════
PHASE 4: CREATE TEAM TASK ASSIGNMENTS
═══════════════════════════════════════════════════════════════

Create d:\SIH-26\tasks\ directory with 6 files:

For EACH person (P1-P6), create a self-contained task file that includes:

### STRUCTURE OF EACH TASK FILE:
```
# [Role Name] — [Person Code]
## Owns: [subsystem list]

## Day-by-Day Plan
### Day 1: [tasks with exact file paths to create]
### Day 2: [tasks]
... through Day 7

## Files You Create (exact paths)
- src/[subsystem]/file1.py — [one-line description]
- src/[subsystem]/file2.py — [one-line description]

## Interfaces
- You PRODUCE: [schema types you output]
- You CONSUME: [schema types you receive from others]
- You NEED FROM: [person] by [day]: [what]

## Claude Code Prompt
[A ready-to-paste prompt for this person's Claude session that:
 - References CLAUDE.md and their task file
 - States their role and subsystem
 - Lists exact files to build
 - Says "Start with [first_file] now"
 - Is optimized for token efficiency]

## If Claude Is Offline
[Key docs links, pseudocode for core algorithms, enough to code without an LLM]
```

### ROLE ASSIGNMENTS:
P1 (ARCHITECT/Lead): NYAYA (path integral + emission prior + latent source + posterior + calibration) + evaluation harness + integration
P2 (ML-VISION): NETRA (U-Net training on Zenodo+ESSD, 3-channel VV+VH+wind, look-alike rejection, TorchScript export) + CHHAYA (xView3 wrapper)
P3 (PHYSICS): PRATIVARTAN (OpenDrift backward ensemble → Φ field) + PRAVAAH (forward drift → landfall) + forcing data (CMEMS/ERA5 fetch + cache)
P4 (BACKEND): FastAPI + AIS pipeline (ingest + interpolate + synthetic) + PostgreSQL/PostGIS + SMRITI (case store + hotspots) + ABHIYAN (greedy tasking)
P5 (FRONTEND): React + Vite + MapLibre GL + deck.gl (Φ heatmap, particle animation, vessel tracks, posterior panel, landfall clock, judge controls)
P6 (PRODUCT): Demo script (6 moments from Section 15), data caching (SAR scenes + forcing + AIS for 3 demo cases), evidence slides, backup video recording, rehearsal coordination

### KEY CONSTRAINTS FOR TASK FILES:
- Include the EXACT model architecture for P2 (U-Net, ResNet34 encoder, 3 channels, 2 heads, Dice+BCE loss)
- Include the EXACT Φ format for P3 (3D histogram as .npz, not KDE)
- Include the EXACT path integral formula for P1 (L_k = Σ Φ(x_k(t), y_k(t), t) × Δt)
- Include ALL API routes for P4 (POST /detect, POST /attribute, POST /forecast, GET /cases, POST /toggle-transponder)
- Include the deck.gl layer types for P5 (HeatmapLayer for Φ, ScatterplotLayer for particles, PathLayer for tracks)
- Include the 6 demo moments script for P6 (from Section 15.2)
- Each task file must have enough detail that the person can build WITHOUT reading anyone else's task file
- The only shared dependency is src/common/schemas.py — if everyone follows those types, integration is automatic

═══════════════════════════════════════════════════════════════
PHASE 5: VERIFY
═══════════════════════════════════════════════════════════════

After creating everything:
1. Verify all __init__.py files exist
2. Verify schemas.py imports cleanly (run: python -c "from src.common.schemas import *")
3. Verify config.py imports cleanly
4. List the complete file tree you created
5. Print a summary: "Project bootstrapped. [N] files created. Next: each team member opens their tasks/P[N]_*.md and starts building."

═══════════════════════════════════════════════════════════════
CONSTRAINTS
═══════════════════════════════════════════════════════════════
- Do NOT use web search, browser, image generation, or any external tools — ONLY read files and write files
- Do NOT write subsystem implementation code (no model.py, no engine.py, no train.py) — only skeleton + schemas + task docs
- Do NOT summarize the master context back to me — just absorb and build
- Do NOT ask questions — make decisions and document them in CLAUDE.md
- Do NOT run any commands except for verifying imports (python -c "...")
- Python 3.10+, type hints, Pydantic v2, no tutorials, no excessive comments
- Follow the tech stack from Section 14 EXACTLY — do not substitute anything
- Keep CLAUDE.md under 100 lines — it's read at the start of every future session
- Optimize everything for a 6-person team with limited Claude tokens
- Minimize token usage: no explanations between file writes, no progress updates, just create files silently and give a final summary
```

---

## WHAT THIS PROMPT DOES

```
INPUT:  VARUNA_MASTER_CONTEXT.md (already exists)
        ↓
CLAUDE READS IT
        ↓
CREATES:
  ├── CLAUDE.md                  ← project memory for all future sessions
  ├── requirements.txt           ← all dependencies
  ├── .env.example               ← config template
  ├── docker-compose.yml         ← infra stack
  ├── src/common/schemas.py      ← THE shared contract (most important file)
  ├── src/common/config.py       ← settings loader
  ├── src/common/geo_utils.py    ← coordinate math
  ├── src/common/logging.py      ← structured logging
  ├── src/*/\_\_init\_\_.py      ← empty packages for all subsystems
  ├── tasks/P1_ARCHITECT.md      ← Lead: NYAYA + evaluation + integration
  ├── tasks/P2_ML_VISION.md      ← NETRA training + CHHAYA
  ├── tasks/P3_PHYSICS.md        ← PRATIVARTAN + PRAVAAH + forcing
  ├── tasks/P4_BACKEND.md        ← API + AIS + DB + SMRITI
  ├── tasks/P5_FRONTEND.md       ← React + MapLibre + deck.gl
  └── tasks/P6_PRODUCT.md        ← Demo + data + slides + rehearsal
        ↓
EACH TEAMMATE opens their tasks/P[N]_*.md
        ↓
Finds their Claude prompt → pastes it → builds their subsystem
        ↓
Day 4: everyone's code connects through schemas.py → integration
        ↓
Day 7: ship
```

## WHY ONE PROMPT

- Only ONE input file needed (VARUNA_MASTER_CONTEXT.md)
- Claude CREATES the CLAUDE.md (not us pre-writing it)
- Claude RETHINKS the architecture based on hackathon constraints
- Claude DECIDES the cut order and documents reasoning
- Every team member gets a self-contained task file with their own Claude prompt
- If Claude goes offline, the task files have enough detail to code manually
- schemas.py is the glue — follow the types and integration is free
