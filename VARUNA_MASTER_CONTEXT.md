# VARUNA — Complete Project Context Document
## SIH 2026 · Problem Statement SIH26143 · Master Brief v1.0

---

## 0. HOW TO USE THIS DOCUMENT

This is a **complete, self-contained context dump** for the VARUNA project. Anyone — a human teammate or an LLM — should be able to read only this file and understand the entire plan well enough to start working, without any prior conversation.

**If you are an LLM reading this:** treat every section as established project context. The decisions here were made after a full screening of all 172 SIH 2026 software problem statements, a prior-art and patent sweep, and a verified data audit. Do not re-litigate settled decisions unless new evidence is presented. Sections marked **[HONESTY RULE]** are non-negotiable constraints on what we are allowed to claim — respect them strictly.

**Status:** Design complete. Implementation not started. Next action is the Week-1 go/no-go experiment in Section 17.

---

## 1. THE PROBLEM STATEMENT (VERBATIM)

| Field | Value |
|---|---|
| **PS ID** | SIH26143 |
| **Title** | Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible for the spill. |
| **Organisation** | National Technical Research Organisation (NTRO) |
| **Category** | Software |
| **Theme** | Space Technology |
| **Idea submission deadline** | 20 September 2026 |

### 1.1 Background (verbatim)

> "Marine oil spills inflict great damage on marine ecosystems and several times remains un-attributable to the vessel causing such spills. Leveraging satellite imagery along with AIS data will enable detection of oil spills and vessel responsible for the same."

### 1.2 Description (verbatim)

> "The core challenge attempts to facilitate detection of oil spills and also in identifying the polluting vessel using remote sensing satellite data, such as SAR and EO imagery and AIS data. Participants are to design an intelligent automated pipeline to do the following: (a) Detect and characterise the oil spill and calculating geometric properties and age if feasible. (b) Using oceanographic and meteorological data, it is envisaged to trace the slick towards the origin point and time, predict the future flow of the slick, and (c) analyse and attribute the spill to a vessel using historic AIS data to reconstruct vessel traffic around the origin window in space and time. The irrelevant traffic is to be filtered out and potential suspect vessels are to be scored considering various aspects such as proximity, trajectory, behavioural anomalies etc."

### 1.3 Expected Solution (verbatim)

> "An automated detection and hindcasting machine learning model that identified oils slicks from satellite imagery, mapping their drift paths backward and forward. It also ranks potential culprit vessel based on spatio-temporal correlation with AIS data. A suitable visual interface is also to be developed."

### 1.4 Resources named by SIH (verbatim)

> **AIS Data:** "Format of AIS data can be obtained from sample AIS data available to https://marinecadastre.gov/accessais/." — "Real AIS if available may be used else synthetic data can be prepared for the region of oil spill to demonstrate the functioning of the algorithm."
>
> **Satellite Imagery:** "Zenodo - Sentinel-1 SAR Oil Spill..."

### 1.5 CRITICAL READING OF THE PS

**The PS explicitly asks for backward drift tracing.** It says "trace the slick towards the origin point and time" and asks for suspects "scored considering... proximity, trajectory, behavioural anomalies."

**Consequence:** backward tracing is *the assignment*, not our innovation. Every competing team will do a backtrack and a proximity score. Our differentiation must live in **how** the backtrack and the scoring are done (probabilistic, calibrated, with a latent hypothesis) — not in the fact that we do them at all. This distinction must be articulable in one sentence under questioning.

**Verification note:** `sih.gov.in/sih2026PS` returns HTTP 403 to automated fetches. All PS text above was verified field-by-field against a same-day synced mirror of the official portal.

---

## 2. TEAM PROFILE

Six-person team. The lead (document owner) is AI/ML lead, technical lead, system architect, research lead, and backend/integration contributor.

**Lead's strengths:** Python, NumPy, Pandas, Scikit-learn, PyTorch, deep learning, NLP, computer vision, Transformers, embeddings, multimodal AI. RAG/BM25/dense+hybrid retrieval, semantic search. Agentic AI: planners, tool use, memory, orchestration, model routing, multi-agent. RL: Bellman, Monte Carlo, TD, Q-learning, DQN, Double DQN, REINFORCE, policy gradients, actor-critic, PPO, routing, optimization, planning, sequential decision-making, world-model-style reasoning. Engineering: backend, APIs, inference pipelines, data pipelines, architecture, integration, experimentation, deployment.

**Team covers:** AI/ML, backend, frontend, UI/UX, research/data, integration, testing, product/demo.

**Domain stretch required:** ~25% — ocean drift physics and SAR interpretation. This is a *scientific* stretch, not a different engineering discipline, which is why this PS was selected over alternatives requiring embedded/RF/mechanical expertise.

---

## 3. THE REAL-WORLD PROBLEM

### 3.1 The physical story

A ship's engine room accumulates **bilge water** — an oily mix of leaked lubricant, fuel and seawater. MARPOL Annex I requires it be processed through an oily-water separator to below 15 ppm before discharge, or held and delivered to a port reception facility. Both cost money and time. Some operators simply open a valve at night, well offshore.

The discharge leaves a film microns thick. That film **damps the capillary waves** that scatter radar energy back to a satellite. Where oil sits, the sea stops scattering and appears dark in SAR imagery. This is the entire physical basis of SAR oil detection — and also its weakness, because anything else that flattens the sea surface produces the same dark patch: low wind, algal blooms, natural seeps, rain cells, ship wakes. These are **look-alikes**, and discriminating them is the hardest perception problem in this PS.

The slick then moves. It advects with surface currents, is pushed by roughly 3% of wind speed, spreads under gravity and viscosity, and weathers. By the time a satellite passes overhead — hours or days later — the slick is elsewhere, deformed, and the ship is a hundred nautical miles away.

### 3.2 The deepest underlying problem (one sentence)

> Oil is a **drifting, deforming record of a crime whose timestamp and location have been erased by the ocean** — and every deployed tool tries to identify the culprit by looking at where the evidence *ended up* rather than reconstructing where it *began*.

### 3.3 Severity and enforcement gap

- SkyTruth cites an estimate of **5,000–7,500 vessels discharging untreated bilge annually**, against **23 corporate convictions in the United States in 2016**. *(US figure, cited as illustrative of the global enforcement gap — NOT an Indian statistic.)*
- Chronic operational discharge exceeds headline tanker accidents in aggregate volume, and is entirely deliberate — therefore **deterrable**, which accidental spills are not.

### 3.4 Why India, why now

- **Geography:** India sits astride the Gulf → Malacca tanker artery. ~7,500 km coastline. Dense traffic through the Gulf of Kutch, Mumbai High, and the Palk Bay approaches.
- **Revisit sparsity is the crux:** Sentinel-1 revisit over the Indian EEZ is a matter of days, not hours (thinner since the loss of Sentinel-1B). **This is why India's default case is the aged slick.** Europe, with dense CleanSeaNet tasking, gets the fresh case often enough that geometric matching works. India mostly does not.
- **Institutional gap:** ITOPF's country profile for India describes surveillance as fixed-wing aircraft and helicopters from the Navy and Air Force. It describes **no satellite attribution capability** and contains **nothing on vessel identification or prosecution mechanisms**. The Indian Coast Guard is the designated national authority under the National Oil Spill Disaster Contingency Plan (NOS-DCP, promulgated 1996, last updated ~2014).

---

## 4. STAKEHOLDERS

| Actor | Responsibility | Information needed | Decision made | Current pain |
|---|---|---|---|---|
| **ICG District HQ duty officer** | Statutory first responder; NOS-DCP coordination | Is this real oil? Where from? Which ship? | Task a Dornier sortie / launch an OPV / stand down | Has a picture of a slick and no way to name a ship |
| **NTRO geospatial analyst** *(PS owner)* | Maritime domain awareness from SAR + AIS | Fused, prioritised leads instead of raw scenes | What to escalate | Manual scene-by-scene interpretation does not scale |
| **DG Shipping enforcement officer** | MARPOL Annex I detentions and penalties | Defensible evidence chain with stated confidence | Detain at next port call; inspect Oil Record Book | Cannot act on "the nearest ship probably did it" |
| **Dornier / ALH aircrew** | Verification overflight | A bearing and a search box worth flying | Where to fly, when | Sorties are expensive; a bad box wastes one |
| **State Pollution Control Boards** | Shoreline impact, compensation | Forecast of where the slick lands | Pre-position booms; issue advisories | Warned only when oil is already ashore |
| **Fishing communities** | — | Advisory | Whether to sail | Bear the loss; nobody is ever charged |

---

## 5. CURRENT WORKFLOW AND THE GAP

```
EVENT        Vessel discharges bilge, ~02:00, 60 nm offshore. No witness.
   ↓
DATA ARRIVES Sentinel-1 pass hours-to-days later.          [automated]
   ↓
PROCESSING   Scene calibrated, speckle-filtered, land-masked. [automated]
   ↓
ANALYSIS     Analyst or U-Net flags a dark patch.          [semi-automated]
             Is it oil, low wind, or algae?                ← MANUAL, error-prone
   ↓
   ▼▼▼  THIS IS WHERE VARUNA INTERVENES  ▼▼▼
   Reconstruct the origin. Score the traffic. State confidence.
   ↓
HUMAN        "Any ship on the slick?" If no → case closed. ← DECISION BOTTLENECK
DECISION
   ↓
ACTION       Usually none. Occasionally a speculative sortie.
   ↓
RESULT       "Source unknown."
   ↓
RECORD       Filed. No feedback loop. Nothing learns. Offender repeats. ← NO MEMORY
```

**We do not replace detection and we do not replace the officer.** We insert one missing inferential step between "a slick exists" and "a human decides," and we close a feedback loop that currently does not exist.

---

## 6. PRIOR ART — WHAT ALREADY EXISTS

**[HONESTY RULE] This section is the most important in the document. Attribution is NOT unsolved. Anyone claiming otherwise will be destroyed in Q&A.**

### 6.1 SkyTruth Cerulean — the closest prior art

- Open source, **Apache-2.0**, live in production
- Code: https://github.com/SkyTruth/cerulean-cloud
- Methods: https://skytruth.org/cerulean/methods
- API: https://skytruth.org/cerulean-api/
- **Detection:** ResNet34-based U-Net on Sentinel-1, 80 m resolution, overlapping 512×512 tiles
- **Vessel association:** three geometric metrics — *parity* (slick length vs projected length along an AIS track, i.e. parallelism), *proximity* (distance from slick head to nearest point on the vessel trajectory), *temporality* (timestamp of nearby AIS broadcasts relative to image capture). AIS window: **8 hours before, 6 hours after** image capture.
- **Infrastructure association:** distance-decay probability to offshore oil/gas points
- **Dark vessel detection:** objects >30 m within 50 km of a slick, scored by distance and angular alignment with predicted vessel paths
- **CRITICAL:** its own methods page states it uses **no physical ocean drift modelling and no backward trajectory analysis**. It explicitly disclaims definitive attribution: detections are "potential — not confirmed" pollution events.

### 6.2 EMSA CleanSeaNet

- Operational since 2007, EU-wide; https://www.emsa.europa.eu/csn-menu.html
- Fuses SAR slick detections with AIS (direct regional-server AIS access since late 2008), delivering analysis ~30 min after satellite pass
- Flags vessels "**still connected to the slick**" — i.e. the fresh case
- Acknowledged limits: SAR alone cannot confirm mineral oil; aerial overflight required to confirm type/thickness

### 6.3 HELCOM Seatrack Web (SMHI)

- Operational ~20 years; https://stw.smhi.se/
- Forward **and backward** drift modelling explicitly for "prediction and identification of illegal polluters," cross-referenced against AIS
- **This is the key precedent to design around and to cite.** Deterministic backtracking; no published multi-suspect probabilistic ranking or latent-source treatment.

### 6.4 Bayesian spill source inversion (academic)

- *Iterative data-driven construction of surrogates for an efficient Bayesian identification of oil spill source parameters from image contours*, Computational Geosciences, 2024 — https://link.springer.com/article/10.1007/s10596-024-10288-9
- Estimates ~5 source parameters from spill image contours using polynomial chaos surrogates; ~100× speedup over direct sampling
- **Contains no vessel or AIS linkage whatsoever.** Synthetic experiments only.

### 6.5 Patents

- **CN103177608A** (Shanghai Maritime University, filed 2013-03-01, published 2013-06-26, status: **deemed withdrawn**) — "Offshore suspicious ship and ship oil contamination discovering system." Claims a system integrating VTS radar, shore AIS, satellite AIS and SAR. Does not clearly claim backward drift modelling or suspect ranking.
- No other verified patent found covering drift-backtracking for spill source attribution. **The patent search is incomplete** — a proper CPC-class search on Espacenet (G01S13/86, G06V20/13, G08G3/00) is still outstanding.

### 6.6 Commercial

KSAT (Kongsberg) — SAR oil spill + vessel detection services. Windward — AIS-gap/dark-activity risk scoring. HawkEye 360 — RF geolocation of non-broadcasting vessels. Global Fishing Watch / Skylight — hosts Cerulean, MDA platform. **None publishes drift-based probabilistic spill attribution.**

### 6.7 UNREAD PRIOR ART — OPEN RISK

**"A new ship tracing technology from oil spills based on multi-source data"**, Marine Pollution Bulletin, 2024 (PMID 39146713, DOI path S0025326X24007859). Publisher blocks automated access. **This is the single closest piece of prior art and it has not been read.** Obtain it through a college library before finalising any novelty claim. If it contains ensemble reverse advection with probabilistic multi-suspect ranking, our contribution narrows to the latent-source term alone.

### 6.8 THE SURVIVING GAP

| | |
|---|---|
| **Current state** | SAR detection is commodity. Vessel shortlisting exists and is free. |
| **Existing capability** | Geometric matching answers *"which ship is lying alongside this slick?"* |
| **Remaining limitation** | Nothing operational answers *"which ship passed through the place this slick came from, at the time it came from there — and how confident are we?"* Drift physics and AIS reasoning live in separate literatures. |
| **Why it matters** | With 6–12 day Sentinel-1 revisit over the Indian EEZ, the fresh-slick case is the *rare* one. India's operational default is the aged slick — precisely the case every deployed tool fails on. |
| **Not adequately solved** | (i) uncertainty-aware reverse drift feeding vessel attribution; (ii) calibrated posteriors fit for evidentiary use; (iii) the dark-vessel case treated as a *hypothesis to be tested* rather than a heuristic afterthought. |

---

## 7. WHAT WE ARE BUILDING — VARUNA GRID

**Name:** VARUNA — in the Vedic tradition, god of the ocean *and* of ṛta (cosmic law); the deity who binds those who break it. Appropriate for a maritime polluter-attribution system, and it lands well with an Indian government audience. (Sanskrit acronyms are standard in Indian defence: NETRA, RUSTOM, PRAHAR are real systems.)

**Full name:** VARUNA GRID — National Marine Pollution Watch & Response Grid

**One-line value proposition:** Turns a drifting slick into a ranked, calibrated list of suspect vessels — or an evidence-backed statement that the culprit was running dark — and then warns the coast, tasks the aircraft, and builds the case.

**If the frontend disappeared, what remains:** A service that ingests `(SAR scene, timestamp, AIS window)` and returns a posterior over vessels, a serialised origin probability field, and an evidence manifest. **That API is the product.** The map is how humans read it.

### 7.1 THE STRATEGIC POSITIONING

Every competing team will build the same three boxes: segment → backtrack → rank ships. They will all demo the same screen.

**The winner is the team whose system obviously continues after the answer** — forecasting where oil lands, deciding which asset to launch, producing the prosecution file, remembering the offender.

That is the difference between "we detect spills" and "**we run maritime pollution enforcement for India.**" Same core technology, completely different thing to sit in front of.

**Positioning line (memorise):**
> "Today, a spill is detected and the file is closed as *source unknown*. VARUNA closes the loop: it names the ship, warns the coast, launches the aircraft, and builds the case — in the eleven minutes before the duty officer finishes his tea."

---

## 8. THE CORE TECHNICAL MECHANISM

**Name:** Reverse-Drift Posterior Attribution (RDPA) with a latent dark-vessel hypothesis.

**Core idea:** Stop asking "which track looks like this slick?" Instead, reconstruct *where and when the oil was released* as a probability field, then score every candidate vessel by how much of that field its trajectory actually explains — and score, in the same normalised competition, the hypothesis that no observed vessel did it.

### 8.1 Step-by-step

```
INPUT    Sentinel-1 SAR scene · slick mask · ERA5 wind · CMEMS surface currents
         · AIS tracks in a wide space–time envelope

STEP 1   Segment slick; extract contour, area, elongation, and a coarse AGE PRIOR
         from spreading geometry + wind history (thin/wide/diffuse ⇒ older).
         The age prior is a DISTRIBUTION, never a point estimate.

STEP 2   ENSEMBLE REVERSE ADVECTION. Seed N particles across the slick mask.
         Integrate BACKWARD in time under M perturbed forcing realisations
         (wind-drift/leeway coefficient, current field member, horizontal
         diffusivity — each sampled from its uncertainty range).
         Result: N×M backward trajectories, not one streamline.

STEP 3   Accumulate a 4-D ORIGIN PROBABILITY FIELD  Φ(x, y, t)
         — the posterior over release location and release time.

STEP 4   PATH-INTEGRAL LIKELIHOOD. For each AIS candidate track k, integrate Φ
         along that vessel's own space–time path:
               L_k = ∫ Φ(x_k(t), y_k(t), t) dt
         weighted by an emission prior π_k (vessel type, size, speed profile,
         loitering, AIS gap behaviour).

STEP 5   LATENT-SOURCE HYPOTHESIS L₀. Compute the residual mass of Φ that NO
         observed track passes through. High residual ⇒ the field says oil came
         from somewhere no broadcasting ship ever was.

STEP 6   Normalise {L₀, π₁L₁ … π_kL_k} into a posterior.
         Calibrate on simulated truth (isotonic regression / temperature scaling).

OUTPUT   Ranked vessels with CALIBRATED probabilities, or "latent source
         dominant" + an inferred pseudo-track for the dark ship, usable as an
         SAR/RF sensor-tasking cue. OR "INCONCLUSIVE" if the posterior is flat.

FEEDBACK Confirmed interceptions and lab fingerprint matches update the emission
         prior and recalibrate; every run stores its Φ field as evidence.
```

### 8.2 Why this formulation

It is the only one that **degrades gracefully with slick age**: as the origin field widens, probabilities spread and the system says so, instead of confidently naming the nearest innocent ship.

### 8.3 Claim-like substance (NOT a legal claim)

> A method for attributing a detected marine slick to a source vessel, comprising: generating a probability field over origin space and time by ensemble reverse advection of a segmented slick under perturbed environmental forcing; evaluating each candidate vessel trajectory as a path integral over said field to yield a per-vessel likelihood; and computing a normalised posterior over candidates that **includes a latent-source hypothesis representing a non-broadcasting vessel**, derived from the residual field mass unexplained by any observed trajectory — and, when that hypothesis dominates, emitting an inferred source track as a sensor-tasking cue.

### 8.4 The "strip the UI" test

Remove the map, the dashboard and the branding, and what remains is: *ensemble reverse advection → 4-D origin field → path-integral scoring of trajectories → normalised posterior with an explicit unobserved-source term.* That is a mechanism, and it is the invention.

---

## 9. THE EIGHT SUBSYSTEMS

| # | Name | Function | What it does | Build cost |
|---|---|---|---|---|
| 01 | **PRAHARI** | Persistent EEZ Watch | Continuously ingests every Sentinel-1 pass over the Indian EEZ, tiles, detects, triages. A standing watch, not "upload an image." Answers "does it scale?" | Low — scheduler over Copernicus API |
| 02 | **NETRA** | Slick Detection & Look-alike Rejection | U-Net over VV+VH with ERA5 wind as an extra input channel. Outputs mask, class (oil/look-alike), confidence. | Medium — train before arrival |
| 03 | **PRATIVARTAN** ★ | Reverse-Drift Origin Engine | OpenDrift ensemble backwards under perturbed forcing → Φ(x,y,t). The most visually arresting element of the demo. | Medium — OpenDrift does the physics |
| 04 | **NYAYA** ★ | Attribution & Dark-Source Hypothesis | Path-integral scoring of AIS tracks against Φ, weighted by behavioural priors, competed against the latent hypothesis. Calibrated output, or *inconclusive*. | Medium — mostly maths, not ML |
| 05 | **CHHAYA** | Dark Vessel Resolver | xView3 pretrained SAR ship detector over the same scene, cross-referenced with AIS. Gives the latent hypothesis a face. | Low — open model, open weights |
| 06 | **PRAVAAH** | Impact & Landfall Forecast | Same drift engine, positive timestep. Projects 24–72 h onto the coast: which beach, which fishing ground, how many hours until arrival. | Very low — one extra OpenDrift call |
| 07 | **ABHIYAN** ★ | Response Asset Tasking | Given Φ, suspects, available assets (Dornier, OPV, station boats), endurance and sea state — computes which asset, which search box, what pattern, to maximise probability of confirmation per hour flown. Genuine optimal-search-allocation (same family as US Coast Guard SAROPS). | Low for greedy/LP version |
| 08 | **SMRITI** | Offender Intelligence & Hotspot Memory | Stores every case with its Φ and outcome. Repeat-offender graph, pollution-corridor heatmap, pre-emptive vessel risk scores / watchlist. | Low — PostGIS queries |

### 9.1 Two thin supporting layers

- **PRAMAN** — Evidence pack. One-click MARPOL Annex I case file: scene IDs, model versions, forcing versions, Φ snapshot, posterior, chain of custody, checksums. *Answers "could this stand up in court?"*
- **SETU** — Dissemination. Routes alerts to ICG station, DG Shipping, State Pollution Control Board, and multilingual SMS/app push to registered fishermen in the projected impact zone. *Costs an afternoon; changes the emotional register of the entire demo.*

---

## 10. SYSTEM ARCHITECTURE

### 10.1 The operational loop

```
   [ PRAHARI ]     every Sentinel-1 pass over the EEZ, automatically
        ↓
   [ NETRA ]       oil, or a look-alike?          → confidence, rejected FPs
        ↓
   [ PRATIVARTAN ] where did it come FROM?        → Φ(x,y,t) origin field
        ↓                                      ↘
   [ NYAYA ]       who did it?                     [ CHHAYA ] …or who was hiding?
        ↓                                      ↙
   [ PRAVAAH ]     where will it LAND, and when?  → named coast + countdown
        ↓
   [ ABHIYAN ]     what do we DO right now?       → asset + search box + ETA
        ↓
   ── HUMAN ──     duty officer approves / overrides / marks inconclusive
        ↓
   [ SETU ]        ICG station · DG Shipping · State PCB · fishermen SMS
        ↓
   ── REALITY ──   overflight result · oil fingerprint · Oil Record Book audit
        ↓
   [ PRAMAN ]      case file sealed, versioned, prosecutable
        ↓
   [ SMRITI ]      outcome recalibrates NYAYA · offender graph grows
        ↓
        └──────── the system is now better than it was ────────┘
```

### 10.2 Technical layer stack

```
REAL WORLD      Vessel discharges bilge, 02:00, 60 nm off Chennai
      ↓
DATA / EVENTS   Sentinel-1 pass · CMEMS currents · ERA5 wind · AIS stream
      ↓
INGESTION       M1 SAR preprocessing · M4 forcing fetch · M6 AIS tracks
      ↓
QUALITY         wind gate · land mask · AIS gap flags · geolocation confidence
      ↓
STORAGE         PostGIS (tracks, cases, Φ metadata) + MinIO/S3 (scenes, fields)
      ↓
PERCEPTION      M2 segmentation + look-alike head
                M9b xView3 dark-vessel detector
                M3 characterisation → age PRIOR (a distribution)
      ↓
PHYSICS         M5 ENSEMBLE REVERSE ADVECTION → Φ(x, y, t)
      ↓
INFERENCE       M7 path-integral likelihoods · M8 emission prior
                M9 latent dark-vessel hypothesis L₀
      ↓
DECISION        M10 calibrated posterior → ranked | "dark" | INCONCLUSIVE
      ↓
WORKFLOW        M14 officer console: Φ overlay, evidence, accept/reject
      ↓
HUMAN ACTION    Dornier tasking · OPV divert · DG Shipping port-call hold
      ↓
VERIFICATION    Overflight result · oil fingerprint · Oil Record Book audit
      ↓
FEEDBACK        M12 outcome written back → recalibrate M10, retrain M8
      ↓
HISTORY         Recidivism graph: which vessels and corridors recur
```

### 10.3 Module detail

| Module | In → Out | Technology | Failure mode → fallback | Priority |
|---|---|---|---|---|
| **M1** SAR preprocessing | GRD scene → calibrated, speckle-filtered, land-masked tiles | ESA SNAP / pyroSAR; GSHHG coastline | Bad orbit file → restituted orbit, flag geolocation confidence | CORE |
| **M2** Segmentation + look-alike head | Tiles + ERA5 wind channel → mask, class, confidence | U-Net / DeepLabv3+, PyTorch | Low confidence → route to human confirm; never auto-escalate | CORE |
| **M3** Slick characterisation | Mask → area, elongation, orientation, **age distribution** | OpenCV morphometry + small regressor | Weak signal → widen the age prior (degrade honestly) | CORE |
| **M4** Forcing fetcher | Bbox + time → currents, wind fields | `copernicusmarine`, CDS API, cached NetCDF | Outage → cached climatology + explicit confidence downgrade | CORE |
| **M5** Reverse-advection ensemble | Mask + forcing + age prior → Φ(x,y,t) | **OpenDrift/OpenOil, negative timestep**, perturbed leeway & diffusivity | Compute blowout → reduce M, report widened uncertainty, never silently truncate | CORE |
| **M6** AIS ingest & track builder | Raw AIS → cleaned, interpolated tracks with gap metadata | Pandas/GeoPandas, PostGIS | Sparse AIS → interpolate *and inflate variance*, never silently | CORE |
| **M7** Path-integral scorer | Φ + tracks → per-vessel likelihood | Numeric integration along interpolated trajectories | — | CORE |
| **M8** Emission prior | Vessel metadata + behaviour → prior weight | Rules + gradient boosting: type, size, AIS gaps, loiter, speed drop | Unknown vessel type → uninformative prior | CORE |
| **M9** Latent-source hypothesis | Φ residual mass + dark-vessel detections → L₀ and inferred track | Residual integration + xView3 detector | — | CORE |
| **M10** Posterior + calibration | Likelihoods → calibrated probabilities | Normalisation + isotonic regression on simulated truth | Flat posterior → return **"inconclusive"** | CORE |
| **M11** Forward drift forecast | Slick + forcing → 24–72 h impact projection | OpenDrift forward (same engine, positive timestep) | — | IMPORTANT |
| **M12** Case store & recidivism | Case → persisted Φ, posterior, outcome; spatial NN over history | PostGIS + object store | — | IMPORTANT |
| **M13** Evidence manifest | Case → signed report: model hashes, forcing versions, parameters, Φ snapshot | Deterministic serialisation + checksum | — | IMPORTANT |
| **M14** Officer console | Case → map, Φ overlay, ranked suspects, accept/reject | React + MapLibre + deck.gl | — | CORE |
| **M15** Report drafting | Structured outputs → readable incident narrative | Local LLM, all numbers injected not generated | Unavailable → template fallback | OPTIONAL |

**Note what is absent:** no vector database, no agent framework, no knowledge graph, no microservice mesh. Fifteen modules, four of which are optional or important-not-core. Everything present is load-bearing.

---

## 11. ML vs NON-ML DECISIONS

Roughly a third of this system is machine learning. The core inference is deliberately **not**.

| Subproblem | Recommended approach | Why |
|---|---|---|
| **Slick segmentation** | U-Net / DeepLabv3+ on VV+VH | Genuine ML need — texture and context, not intensity alone |
| **Look-alike rejection** | Multi-class head + **ERA5 wind as an input channel** | Feeding wind into the network is the cheapest large win — low-wind look-alikes are physically identifiable from context the image alone lacks |
| **Slick age** | Small regressor → outputs a **PRIOR distribution**, not a point | PS says "if feasible." Let the ensemble consume the distribution |
| **Dark vessel detection** | xView3 reference detector, fine-tuned | Solved problem, open data, open model. Do not reinvent |
| **Backward drift** | **NOT ML** — OpenDrift ensemble | Physics is known and trusted. Learning it would be strictly worse and destroy auditability |
| **Attribution scoring** | **NOT ML** — path-integral likelihood | A learned ranker needs labels that do not exist. The probabilistic formulation needs none and is inspectable in court |
| **Behavioural anomaly** | Rules + gradient boosting as a PRIOR term | Interpretable features beat a black box a defence lawyer will attack |
| **Calibration** | Isotonic / temperature scaling on simulated truth | Turns a score into a probability that means something. A headline metric, not plumbing |

### 11.1 Three explicit NOs

**REINFORCEMENT LEARNING — NO (for the core).**
Attribution is *inference about a past event*, not sequential decision-making. There is no policy to learn, no environment to act in, no reward to maximise. Forcing RL here would be exactly the "AI for the sake of AI" failure mode.
*The one legitimate adjacent framing:* **ABHIYAN** — deciding where to point the next SAR acquisition or send the aircraft given an uncertain origin field — is a genuine sequential information-gathering / optimal-search-allocation problem. Build a greedy/LP version for SIH; RL framing belongs in the post-SIH roadmap.
*What does transfer:* Monte Carlo estimation, importance weighting and posterior reasoning are the mathematical spine of the ensemble and the path integral. The intuition is used; the algorithm is not.

**RAG / VECTOR SEARCH — NO.**
There is no corpus. Nothing here is answered by retrieving text. A MARPOL-regulation chatbot bolted on would be transparent padding.
*One genuine retrieval need, and it is not RAG:* **recidivism lookup** — given a new origin field, find prior cases whose fields overlap the same vessel or corridor. That is a spatio-temporal nearest-neighbour query over a PostGIS table. No embeddings, no LLM.

**AGENTS — NO.**
The pipeline is a fixed, auditable sequence: detect → backtrack → score → present. No branching requires a planner, and non-determinism in an evidence chain is a liability.
*The one defensible LLM use:* drafting the human-readable incident report from structured outputs, with every number **injected** from the pipeline rather than generated. Optional, bounded, must never touch the inference.

---

## 12. DATA SOURCES — VERIFIED

### 12.1 Ready to download now, no registration

| Source | Details | Link |
|---|---|---|
| **Zenodo Sentinel-1 Oil Spill Part I** *(named by the PS)* | 1,200 Sentinel-1 images + masks. TIFF, 2048×2048×2 (VV+VH); masks 2048×2048. Binary segmentation. ~40.9 GB. CC-BY-4.0. Published 17 Dec 2024. | https://zenodo.org/records/8346860 |
| **Zenodo Part II** | Additional validation set. CC-BY-4.0. | https://zenodo.org/records/8253899 |
| **Zenodo Part III** | Test set. CC-BY-4.0. | https://zenodo.org/records/13761290 |
| **Eastern Mediterranean slicks + look-alikes (ESSD 2025)** | **3,225 oil objects across 1,365 image patches + 2,290 patches of look-alikes/other phenomena.** Sentinel-1A/1B, 2019. Dual-interpreter agreement labelling. CC-BY-4.0. **The look-alike set is the single most valuable dataset for us.** | Paper: https://essd.copernicus.org/articles/17/6807/2025/ · Data: https://doi.org/10.1594/PANGAEA.980773 |
| **MarineCadastre AIS** *(named by the PS)* | CSV, daily national files. **US waters only**, 2009→recent. Fields: MMSI, position, SOG, COG, vessel type. US public domain. | https://marinecadastre.gov/accessais/ |

### 12.2 Free with a registration (5 minutes)

| Source | Details | Link |
|---|---|---|
| **Sentinel-1 GRD** | SAFE/GeoTIFF, ~1 GB/scene. OData + openEO + S3 APIs. Global incl. full Indian EEZ, 2014→now. Free. | https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-1 |
| **CMEMS ocean currents — analysis/forecast** | `GLOBAL_ANALYSISFORECAST_PHY_001_024`. NetCDF, 1/12° (~8 km), hourly/daily. Python `copernicusmarine` client. | https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description |
| **CMEMS ocean currents — reanalysis** | `GLOBAL_MULTIYEAR_PHY_001_030`. NetCDF, 1/12°, multi-decade. **Use this for historical case studies.** | https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/description |
| **ERA5 wind** | NetCDF/GRIB, 0.25°, hourly, 10 m u/v components. Global, 1940→now. | https://cds.climate.copernicus.eu/ |
| **xView3-SAR** | Large-scale Sentinel-1 dark-vessel detection benchmark with AIS-derived labels. Reference model open-sourced by Allen AI. | Paper: https://arxiv.org/abs/2206.00897 · Model: https://github.com/allenai/sar_vessel_detect |

### 12.3 Requires an application — APPLY IN WEEK 1

| Source | Details | Link |
|---|---|---|
| **Krestenitis / MKLab oil spill dataset** | JPG + colour-coded masks, ~400 MB, ~1,000 train / 110 test. **5 classes: oil spill, look-alike, land, ship, sea.** Ground truth from EMSA CleanSeaNet, Sep 2015 – Oct 2017. Requires: Terms of Use review, project title + abstract, templated email from an institutional account, supervisor sponsorship for students. Citation required (Krestenitis et al. 2019). | https://m4d.iti.gr/oil-spill-detection-dataset/ |

### 12.4 Software

| Tool | Details | Link |
|---|---|---|
| **OpenDrift / OpenOil** | Python trajectory framework with an oil module. Reads currents/wind/waves from any model, any format, any projection. **Supports backward simulation via a negative time step.** GPLv2. | https://opendrift.github.io/ |
| **Cerulean (baseline)** | Apache-2.0. Legitimate to read and reimplement as our baseline comparator. | https://github.com/SkyTruth/cerulean-cloud |

### 12.5 NOT AVAILABLE

| Gap | Reality | Mitigation |
|---|---|---|
| **Indian EEZ AIS** | Restricted / commercial. Not obtainable by a student team. | **The PS explicitly permits synthetic:** "Real AIS if available may be used else synthetic data can be prepared." Develop and validate on real US AIS (real traffic geometry, speed distributions, gap statistics), demonstrate on synthetic Indian-EEZ traffic. **State this openly on the slide.** |
| **Attribution ground truth** (confirmed slick → confirmed guilty vessel) | **Does not exist publicly anywhere.** | **Generate it by simulation** — see Section 13. This is a feature, not a bug: it is precisely why this contribution is unclaimed. |

---

## 13. EVALUATION PLAN

### 13.1 The simulation harness (the backbone)

Pick a real AIS track → release simulated oil at a known point and time → advect forward under real currents and wind → render a realistic slick → hand the system **only** the slick and the surrounding traffic. Truth is known exactly. Difficulty is a dial we control. Thousands of cases can be generated.

### 13.2 Specification

| Axis | Specification |
|---|---|
| **Baselines** | (1) nearest vessel to slick; (2) **Cerulean's published parity/proximity/temporality scheme, reimplemented** (Apache-2.0, so legitimate — and it is the comparison that matters); (3) single deterministic backtrack, Seatrack-style |
| **Headline metric** | Top-1 and Top-3 attribution accuracy **as a function of slick age** (2 / 6 / 12 / 24 / 48 h) at fixed traffic density |
| **Second axis** | Accuracy vs **traffic density** (5 / 20 / 50 / 100+ vessels in envelope) — reveals whether the posterior is genuinely discriminative |
| **Calibration** | Expected Calibration Error (ECE) and reliability diagrams. **Non-negotiable** — an uncalibrated probability is inadmissible as evidence, and no competing team will report this |
| **Latent-source metric** | Precision/recall on "was this a dark vessel?" — delete the guilty track from AIS and measure detection, against the false-latent rate when the guilty ship IS present |
| **Perception** | IoU / F1 on Zenodo test split; **false-positive rate on the ESSD look-alike set reported separately** — this is the number that shows we understood the real problem |
| **Ablations** | ensemble → single trajectory · path-integral → nearest-point · ± emission prior · ± latent term · ± wind channel · N and M sweeps for the compute/accuracy frontier |
| **Stress tests** | Injected current-field error · AIS gaps 20–120 min · degraded segmentation · two overlapping slicks from different sources · weak-current regimes |
| **Publish failures** | Slow-current cases where Φ stays diffuse; dense shipping lanes where many tracks cross the origin. Showing these earns more credibility than hiding them |

### 13.3 NORTH-STAR KPI

> **Top-1 attribution accuracy at 24-hour slick age with ≥20 vessels in the envelope, subject to ECE < 0.05.**

One number. It fixes the operationally realistic case (a day-old slick in real traffic — India's default), demands the baselines be beaten where they actually break, and the calibration constraint prevents winning by confident guessing.

---

## 14. TECH STACK

| Layer | Choice | Why | Rejected |
|---|---|---|---|
| Drift engine | **OpenDrift / OpenOil** (GPLv2) | Purpose-built, backward-capable, MET Norway maintained, reads CMEMS/ERA5 natively | Custom advection — weeks of work, worse physics, no credibility |
| ML | **PyTorch** + segmentation-models-pytorch | Team fluency; U-Net encoders off the shelf | TensorFlow — no advantage here |
| Geospatial | **rasterio, GeoPandas, xarray, Shapely, pyproj** | Standard scientific-Python geospatial stack; xarray is the right abstraction for NetCDF forcing | GDAL CLI scripting — brittle |
| SAR preprocessing | **ESA SNAP via pyroSAR** | The reference toolchain; calibration and speckle filtering are solved | Hand-rolled calibration — correctness risk for zero gain |
| Backend | **FastAPI** + Celery/RQ workers | Async, typed, containerised; jobs are long-running so they need a queue | Django — heavier than needed; Flask — no async/typing |
| Database | **PostgreSQL + PostGIS** | Spatio-temporal queries over tracks and cases are the whole data model; recidivism lookup is one `ST_DWithin` | MongoDB — weaker geospatial; vector DB — nothing to embed |
| Object storage | **MinIO** (S3 API) | Scenes and Φ fields are large binaries; S3 API keeps cloud/on-prem portability | Filesystem — no versioning or provenance |
| Frontend | **React + MapLibre GL + deck.gl** | deck.gl renders the particle ensemble and Φ heatmap smoothly — **the demo depends on this** | Leaflet — struggles with tens of thousands of animated particles |
| Model serving | **TorchScript / ONNX Runtime** in the worker | Two small models; a dedicated server is overkill | Triton/TF-Serving — operational weight for no benefit |
| Infra | **Docker Compose**, one GPU node | Must run air-gapped on ICG hardware; Compose is honest at this scale | Kubernetes — theatre for a six-person team |
| Experiment tracking | **MLflow** or DVC | Evidence manifests need model and data versions to be reproducible | Spreadsheets — not reproducible |

---

## 15. DEMO PLAN

### 15.1 Six engineered moments

**1. THE WRONG ANSWER.** Load an 18-hour-old slick. Run the *industry-standard geometric baseline* first. It confidently names a ship. Reveal ground truth — **it named an innocent vessel that merely sailed past.** Pause. Then run VARUNA.
*Why: the judge feels the failure before you fix it. Nobody argues with a problem they just watched happen.*

**2. THE BACKWARD BLOOM.** Twenty thousand particles run backwards across the map in real time, drifting 31 km and blooming into a glowing origin field. Do not speed this up. Let it play for a full ten seconds and say nothing.
*Why: the only moment in any SIH26143 demo where the innovation is visible rather than asserted.*

**3. HAND THE JUDGE THE CONTROLS.** "Sir, pick any ship on this screen and switch its transponder off." They click. Re-run. The posterior collapses and flips to **latent source 0.78**, and the system draws the inferred dark track. CHHAYA puts a radar contact on it.
*Why: judges evaluate forty teams. They will remember the one whose system they operated. **Highest-leverage 90 seconds in the entire build — engineer it first.***

**4. THE LANDFALL CLOCK.** Forward drift resolves onto a named stretch of coast with a live countdown: `oil reaches Marina Beach in 31 h 20 m`. The SMS panel fires — multilingual alerts to registered fishing boats in the projected zone.
*Why: converts a radar image into a village. The entire impact score in one screen.*

**5. THE PATTERN REVEAL.** Zoom out from one case to a season. The hotspot map shows discharges clustering in a corridor **just outside territorial waters, between 01:00 and 04:00**. "This is not carelessness. This is a pattern, and it is deliberate."
*Why: stops being a student project and becomes a source of policy intelligence.*

**6. THE HONEST REFUSAL.** Run a weak-current, dense-traffic case. The system returns **INCONCLUSIVE** — and still hands the officer a narrowed search box. "We built a system that can be wrong out loud, because an enforcement tool that always names someone is worse than useless."
*Why: pre-empts the hardest Q&A question and reads as engineering maturity.*

### 15.2 Ten-minute finale script

```
0:00–0:45  THE ROOM. "It is 02:10. A duty officer at Coast Guard District HQ
           has a radar image with a black smear on it. Somewhere out there is a
           ship that did this. Today, he closes the file as SOURCE UNKNOWN."
           Two numbers: 5,000–7,500 vessels dumping bilge a year; 23 convictions.
           [Insert mentor-feedback line here.]

0:45–1:30  WHY IT FAILS. MOMENT 1. Run the standard geometric baseline on an
           18-hour-old slick. It names a ship. Reveal truth — wrong ship.
           "It matched the vessel nearest the oil. But the oil moved."

1:30–3:30  THE GRID FINDS THE ORIGIN.
           · NETRA segments — and rejects a look-alike beside it
           · Currents and wind fields wash in under the slick
           · MOMENT 2. 20,000 particles run backwards. Ten seconds. Silence.
           · Φ blooms 31 km NE. "That is where the oil was born."

3:30–5:00  THE GRID NAMES THE SHIP.
           · 41 AIS tracks appear → collapse to 3 → posterior resolves
           · Vessel A 0.71 · dark 0.14 · rest negligible. Truth: Vessel A.
           · Score breakdown: proximity, trajectory, AIS gap behaviour
           · MOMENT 3. "Sir, switch off any ship's transponder."
             Judge clicks. Re-run. Latent 0.78 + inferred dark track.

5:00–6:30  THE GRID PROTECTS THE COAST.
           · MOMENT 4. PRAVAAH → landfall on a named beach, countdown 31h20m
             → SETU fires multilingual alerts to fishing boats
           · ABHIYAN: "Launch the Dornier from Chennai, this search box, dawn.
             68% probability of visual confirmation, 2.1 flight hours."

6:30–7:30  THE GRID REMEMBERS.
           · MOMENT 5. Season-wide hotspot corridor just outside territorial
             waters, 01:00–04:00. "This is a pattern. It is deliberate."
           · Repeat-offender graph. PRAMAN case file in one click.

7:30–8:45  EVIDENCE.
           · Accuracy-vs-slick-age: baselines fall off a cliff past 6h, we don't
           · Reliability diagram: "when we say 0.7, it is 0.7"
           · MOMENT 6. The inconclusive case.

8:45–10:00 DEPLOYMENT. One GPU. Free open data. Air-gappable. Runs on hardware
           ICG already owns. "Naming the ship is the middle of the job. VARUNA
           does the rest — and every case it closes makes the next one easier."
```

---

## 16. BUILD PLAN

### 16.1 THE RULE

**You do not train models at the finale. You assemble and polish.** Wi-Fi drops, Copernicus rate-limits, and 40 GB does not download at 2 a.m. in a hackathon hall. Teams lose on this, not on ideas.

### 16.2 Pre-built before travelling

- Trained NETRA weights on Zenodo Parts I–III + ESSD look-alikes, exported to TorchScript
- xView3 detector downloaded and running for CHHAYA
- **Cached forcing data** — CMEMS currents + ERA5 wind for 3–4 demo regions/dates, as local NetCDF. **Never depend on a live API during a demo.**
- Cached SAR scenes and pre-computed AIS windows for each demo case
- A pre-computed Φ field for the hero case, so the demo can fall back to replay if the GPU misbehaves
- The simulation harness and the accuracy-vs-age curve (the evidence slide)
- **A recorded 3-minute video of the full working demo.** If the laptop dies, you still present.

### 16.3 Six people, 36 hours

| Role | Owns | Hours 0–12 | Hours 12–24 | Hours 24–36 |
|---|---|---|---|---|
| **Lead** — ML/architect | NYAYA + PRATIVARTAN | Wire ensemble → Φ → path-integral posterior end to end | Latent hypothesis + calibration | Ablations, edge cases, Q&A prep |
| ML #2 | NETRA + CHHAYA | Load pre-trained weights, wire inference, verify look-alike rejection | Geometric properties + age prior | Support demo cases, tune thresholds |
| Backend | PRAHARI, data layer, APIs | PostGIS schema, AIS ingest, job queue | Watch scheduler, SMRITI queries | PRAMAN evidence pack, hardening |
| Frontend | The console | Map, layers, case view — **get the Φ heatmap rendering early** | Particle animation, time slider, **judge controls** | Polish, transitions, fallback replay mode |
| Integration/optimisation | ABHIYAN + PRAVAAH | Forward drift + landfall geocoding | Asset tasking optimiser (greedy first) | SETU alert fan-out, SMS panel |
| Product/demo | Narrative, slides, evidence | Storyboard the 6 moments; build the hotspot dataset | Rehearse; record the backup video | Rehearse again. Then again. |

**Frontend is not a garnish — it is half the score.** The backward bloom, judge controls and landfall clock all live in the UI. Start the Φ heatmap render in hour one, not hour twenty.

### 16.4 Round-by-round strategy

SIH finale runs several mentor and jury passes across the 36 hours. Evaluators explicitly reward teams who **act on feedback** between rounds.

| Round | Show | Ask |
|---|---|---|
| **R1 early** | Loop diagram + working NETRA detection + problem framing. Be honest that attribution is still wiring up | "Sir, for ICG would you rather have one confident name or a ranked list with confidence?" |
| **R2 mid** | The backward bloom working end to end on a real scene. The credibility moment | "What would make this admissible as evidence?" — feeds PRAMAN |
| **R3 late** | Full loop including PRAVAAH landfall and ABHIYAN tasking. Show the accuracy-vs-age curve | "Which of these would your operations room use first?" |
| **Finale** | The polished ten minutes. Open by **naming the mentor feedback you incorporated** | Nothing. Present. |

**High-return move:** In the finale, say *"In round two a mentor asked what would make this admissible. That question is why PRAMAN exists."* Evaluators reward responsiveness explicitly, and most teams never demonstrate it.

### 16.5 Cut order if behind schedule

| Cut | Drop | Why safe |
|---|---|---|
| 1st | SETU SMS fan-out | Mock the panel; story survives on a screenshot |
| 2nd | ABHIYAN full optimiser | Ship greedy nearest-asset; still shows "the system decides" |
| 3rd | PRAHARI live scheduler | Pre-ingest scenes; describe the watch instead of running it |
| 4th | SMRITI live queries | Pre-compute hotspot map as a static layer — looks identical |
| **NEVER** | NETRA · PRATIVARTAN · NYAYA · judge controls · fallback video | These are the demo. Without them there is no argument |

---

## 17. RISKS AND THE FIRST EXPERIMENT

### 17.1 THE CORE TECHNICAL BOTTLENECK

Everything is downstream of one quantity: **the discriminative power of the origin field against local traffic density.**

Formally — after backtracking a slick of age *T* under forcing with error *ε*, does the posterior concentrate enough probability mass on the true vessel to separate it from *N* innocent ships? The origin field widens with *T* and with *ε*. Traffic density adds candidates.

**If the field is 60 km wide and 40 ships crossed it, the posterior is flat and the system is worthless — no matter how good the segmentation is.**

### 17.2 THE FIRST PROOF — DO THIS BEFORE ANYTHING ELSE

**Pure simulation. No SAR imagery at all. One person, roughly one week.**

Synthetic currents → synthetic release → N×M backward ensemble → K synthetic vessel tracks → path-integral posterior. Sweep **slick age × traffic density × forcing error**.

**Go/no-go question:** does top-1 accuracy stay meaningfully above the nearest-vessel baseline at 24 h with 20 vessels?

**If the answer is no, the entire thesis is wrong and you pivot while it is cheap.**

### 17.3 Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **Flat posterior** (see 17.1) | **Critical** | Week-1 simulation sweep before committing |
| Ocean-current accuracy sets a hard floor on origin-field tightness | High | State openly; report inconclusive cases; ~8 km CMEMS grid is a physical limit, not a modelling failure |
| Unread MPB 2024 paper may contain the mechanism | Medium-High | Obtain via college library in week 1 |
| Indian AIS unavailable → "operational" story is aspirational | Medium | Lead with the algorithm and calibration curves, not with a deployment claim |
| Look-alike false positives | Medium | ESSD look-alike training set + wind gating + report FP rate separately |
| Demo fails on the day | Medium | Cached everything + pre-computed Φ + recorded backup video |

---

## 18. [HONESTY RULES] — THINGS WE MUST NEVER CLAIM

These are non-negotiable. Violating them is the fastest way to lose credibility in Q&A or in a paper.

1. **NEVER claim spill attribution is unsolved.** Cerulean and CleanSeaNet do SAR+AIS matching in production. Our claim is narrower: *aged-slick* attribution using drift physics, which Cerulean explicitly does not do.
2. **NEVER claim backward drift tracing is our innovation.** The PS asks for it. HELCOM Seatrack Web has done it for ~20 years. Our contribution is the *probabilistic formulation*: ensemble uncertainty, path-integral scoring, latent hypothesis, calibration.
3. **NEVER present simulated evaluation as operational validation.** Simulation measures whether the *inference* is sound given correct physics. It cannot measure whether the physics matches the real Bay of Bengal. Different claims.
4. **NEVER hide that Indian AIS is synthetic.** The PS permits it. Say it on the slide. A judge who discovers it themselves will punish you far harder than one you told.
5. **NEVER say "patentable."** Only: "potentially patent-relevant," "worth prior-art investigation," "appears differentiated." Patentability requires professional assessment we have not done, and two blockers remain open (the MPB paper and a CPC-class Espacenet search).
6. **NEVER say "real-time."** Sentinel-1 revisit is days. That constraint is *why* we built backward inference. Any team claiming real-time is wrong about the physics.
7. **NEVER claim "no Indian system exists" as fact.** Say "no *publicly documented* system." This is an inference from ITOPF's India profile and public ICG/NRSC material. An NTRO judge may know otherwise.
8. **NEVER let the system name a ship without a human sign-off.** We produce ranked, calibrated leads for an overflight — not verdicts.

---

## 19. GLOSSARY

| Term | Meaning |
|---|---|
| **AIS** | Automatic Identification System — vessels broadcast identity, position, speed, course. Self-reported; can be switched off or spoofed |
| **SAR** | Synthetic Aperture Radar — active radar imaging, works day/night through cloud. Sentinel-1 is the free source |
| **GRD** | Ground Range Detected — the Sentinel-1 product level we use |
| **VV / VH** | SAR polarisation channels (vertical transmit-vertical receive / vertical-horizontal). Both used as input channels |
| **Look-alike** | A dark SAR patch that is not oil — low wind, algal bloom, natural seep, rain cell, ship wake. **The hardest perception problem here** |
| **Φ (Phi)** | The 4-D origin probability field over release location and time, produced by backward ensemble advection. The core data structure |
| **Advection** | Transport of a substance by fluid motion (here, oil moved by ocean currents and wind) |
| **Leeway** | The wind-driven component of drift, roughly 3% of wind speed for surface oil |
| **Ensemble** | Running many simulations with perturbed parameters to represent uncertainty, rather than one deterministic run |
| **Path integral** | Integrating Φ along a vessel's space-time trajectory to get its likelihood of being the source |
| **Latent source / dark vessel** | A ship not broadcasting AIS. Our hypothesis L₀ competes against named vessels in the same normalisation |
| **Calibration / ECE** | Whether a stated probability matches observed frequency. Expected Calibration Error measures the gap. Essential for evidentiary use |
| **MARPOL Annex I** | The IMO convention governing oil pollution from ships. Requires bilge to <15 ppm before discharge |
| **NOS-DCP** | National Oil Spill Disaster Contingency Plan — India's framework, ICG is the coordinating authority |
| **ICG** | Indian Coast Guard — statutory authority for oil spill response, under Ministry of Defence |
| **Oil Record Book** | Mandatory log of all discharge events. Frequently falsified — a key enforcement lever |
| **CMEMS** | Copernicus Marine Environment Monitoring Service — free ocean current data |
| **ERA5** | ECMWF atmospheric reanalysis — free global wind data |
| **OpenDrift / OpenOil** | The open-source Python trajectory model we use for drift, forwards and backwards |

---

## 20. CURRENT STATUS AND NEXT ACTIONS

**Status:** Design complete. Prior art verified. Data audited. Implementation not started.

### Do these five things first, in this order:

1. **Run the discriminability sweep** (Section 17.2) — pure simulation, one person, one week. Does top-1 accuracy hold at 24 h with 20 vessels? Everything else is contingent on that curve.
2. **Start the NETRA training run** on Zenodo Parts I–III + ESSD look-alikes. It must be finished long before travel.
3. **Get the frontend person rendering a Φ heatmap and animated particles over a map.** Half the demo, and it always takes longer than expected.
4. **Build the hero demo case end to end on cached data** — one scene, one slick, one right answer — and freeze it.
5. **Storyboard the six moments and rehearse the judge-controls handover** until it is boring.

### Parallel administrative actions
- Apply for the Krestenitis dataset (institutional email, project abstract, supervisor sponsorship)
- Obtain the Marine Pollution Bulletin 2024 ship-tracing paper via college library

### Closing note

The technology is not the risk. **Every team that loses SIH loses on rehearsal, caching and a demo that would not run.** The system design here is genuinely strong — protect it with preparation.

---

*Document version 1.0 · SIH 2026 · SIH26143 · VARUNA GRID*
*All external facts verified against primary sources at time of writing. Items that could not be verified are explicitly flagged in the text.*
