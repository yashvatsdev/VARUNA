# ROLE 03 — Frontend / Geo

**Owns:** React · MapLibre · deck.gl · officer cockpit · field mode · mission UI · alerts · stakeholder views

Half the evaluation is what a judge sees. You are also the last line of defence on
honesty: if the UI shows a confident number that the pipeline marked DEGRADED, the
architecture failed at your layer.

**You are unblocked from hour one.** ROLE 01 ships a mock `PhiField` + `.npz` on day 1.
Build against mocks; swap to live API on day 4 with no rendering-code changes.

---

## The rule that defines this role

> **Never render a number without its validity state.**

Every posterior, ETA, and probability carries an `EvidenceEnvelope`. If
`validity_state` is `RESTRICTED` or `INCONCLUSIVE`, the UI must not present a vessel
name as an answer — regardless of how high the number is.

---

## Stack (locked)

React 18 · TypeScript · Vite · MapLibre GL JS v4 · deck.gl v9 · TanStack Query ·
Zustand · Tailwind · SSE for progress. No Leaflet, no Mapbox token.

```bash
npm create vite@latest web -- --template react-ts
npm i maplibre-gl @deck.gl/core @deck.gl/layers @deck.gl/aggregation-layers \
      @deck.gl/mapbox @tanstack/react-query zustand recharts
npm i -D tailwindcss postcss autoprefixer
```

Free basemap, no key: `https://tiles.openfreemap.org/styles/positron`.
For the air-gapped demo, self-host an MBTiles regional pack (`tileserver-gl`).

---

## Day-by-day

### Day 1 — scaffold + Φ heatmap
- Vite + TS + Tailwind + MapLibre centred on the Arabian Sea. Something on screen today.
- `src/layers/PhiHeatmapLayer.ts` — deck.gl `HeatmapLayer` over ROLE 01's mock Φ JSON
  (`{lat, lng, weight, time}[]`, ~200×200, 1-hour bins).
- Time slider scrubbing the bins.

### Day 2 — particles + tracks + trust chrome
- `src/layers/ParticleTripsLayer.ts` — `TripsLayer`, cyan, `trailLength: 600`,
  `requestAnimationFrame` at real pace. **Do not speed it up** — this is the one moment
  where the innovation is visible rather than asserted.
- `src/layers/VesselTrackLayer.ts` — `PathLayer`, coloured by posterior once available.
- `src/components/TrustBadge.tsx` — renders `TrustState` + `ValidityState` +
  `DegradationState`. Every panel that shows a number embeds one.

### Day 3 — officer cockpit
- `src/views/Cockpit.tsx` — map + case list + suspect panel + evidence drawer.
- `src/components/SuspectTable.tsx` — ranked candidates with **all six published prior
  sub-scores** and the evidence/prior split. Latent row always visible and styled apart.
- `src/components/DecisionStateBanner.tsx` — `STRONG_LEAD` / `WEAK_LEAD` /
  `NOT_DISTINGUISHABLE` / `LATENT_SOURCE` / `INCONCLUSIVE`, each with its own visual
  treatment. `INCONCLUSIVE` must look like a deliberate result, not an error state.

### Day 4 — live API + judge controls
- Swap TanStack Query fetches to ROLE 02's API. Layer code should not change.
- `src/components/JudgeControls.tsx` — click a vessel → toggle transponder →
  `POST /cases/{id}/toggle-transponder` → posterior re-renders + inferred dark track
  appears. Sub-2-second round trip or the moment dies on stage.
- SSE progress subscription for the pipeline run.

### Day 5 — Φ diagnostics + forecast
- `src/components/PhiDiagnosticsPanel.tsx` — convergence flag, `n_modes`,
  `effective_support_km2`, and **`dominant_assumption`** from the sensitivity block.
  When `multimodal`, draw both lobes and label them competing origins.
- `src/components/LandfallClock.tsx` — countdown as an **interval**, never a point time.
- `src/components/AlertPanel.tsx` — simulated providers carry a visible `SIMULATED` badge
  (threat L-04). Never present a simulated channel as live.

### Day 6 — missions, field mode, evidence
- `src/views/Missions.tsx` — mission FSM states; approval dialog capturing
  `human_approved_by`. AI recommendation and human decision shown **distinctly**.
- `src/views/FieldMode.tsx` — mobile-first, high-contrast, minimal: search box, bearing,
  contact report. Assume poor connectivity.
- `src/components/{ReliabilityDiagram,AccuracyVsAge}.tsx` — the evidence charts.

### Day 7 — failsafe + rehearsal
- `src/components/ReplayPlayer.tsx` — replay a recorded SSE session through the identical
  UI. Static screenshots one level below that.
- Full rehearsal with ROLE 04.

---

## Screens

| View | Purpose | Must show |
|---|---|---|
| **Cockpit** | Officer primary | Map, Φ heatmap, tracks, suspects, decision state, trust badges |
| **Case detail** | Investigation | Timeline, Φ diagnostics, sensitivity, evidence drawer |
| **Missions** | Response | FSM state, asset, approval dialog, AI-vs-human split |
| **Field mode** | On-scene | Search box, bearing, contact report, offline-tolerant |
| **Alerts** | Dissemination | Channel, audience, delivery log, SIMULATED badges |
| **Evidence** | Defensibility | Manifest, hashes, model + forcing versions |
| **Analytics** | Pattern | Corridors, recurrence, reliability diagram, accuracy-vs-age |

## Interfaces

- **CONSUME:** mock Φ JSON (day 1) → live REST (day 4): `Case`, `AttributionResultV2`,
  `PhiField`, `ForwardForecast`, `MissionRecord`, `EvidenceManifest`, SSE events.
- **PRODUCE:** nothing other modules consume. You are the leaf.
- **NEED:** ROLE 01 day 1 — mock Φ format frozen. ROLE 02 day 4 — live API, fast toggle.

## Acceptance criteria

- [ ] Every numeric display carries a trust/validity indicator
- [ ] `INCONCLUSIVE` renders as a deliberate outcome, never an error
- [ ] Multimodal Φ draws both lobes
- [ ] Simulated alert channels visibly badged
- [ ] AI recommendation and human decision visually distinct
- [ ] Judge-control round trip < 2 s
- [ ] Replay mode works with the backend stopped
- [ ] Runs air-gapped (local tiles, no external fetches)

## Do NOT touch

Any `packages/varuna_*` Python module, Docker, CI. Request API changes from ROLE 02
rather than reshaping responses client-side.

## Claude Code prompt

```
Read LLM_IMPLEMENTATION_GUIDE.md and tasks/ROLE_03_FRONTEND_GEO.md. You are ROLE 03,
frontend/geo, owning the officer cockpit, map visualisation, mission UI, field mode,
and alert views.

Stack is locked: React 18 + TypeScript + Vite + MapLibre GL v4 + deck.gl v9 +
TanStack Query + Zustand + Tailwind + SSE. No Leaflet, no Mapbox token.

Hard rule: never render a number without its validity state. Every posterior, ETA and
probability carries an EvidenceEnvelope; if validity_state is RESTRICTED or
INCONCLUSIVE the UI must not present a vessel name as an answer.

You are unblocked — ROLE 01 ships mock Phi JSON today ({lat,lng,weight,time}[]).
Start now: scaffold apps/web with Vite+TS+Tailwind, install the deck.gl/maplibre stack,
render the OpenFreeMap positron basemap centred on the Arabian Sea, then add
PhiHeatmapLayer over the mock data.
```
