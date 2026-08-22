# P5 — FRONTEND
## Owns: The console (M14) — every visual demo moment lives here

Half the score is this UI. The backward bloom, the judge controls and the landfall clock
are the only parts of the innovation a judge actually *sees*. Read `CLAUDE.md` first.

**You are fully unblocked from hour one.** P1 ships a mock Φ `.npz` on day 1 — build
against that and swap the real one in on day 4 without changing a line of rendering code.

---

## Day-by-Day

### Day 1 — scaffold + basemap
```
npm create vite@latest varuna-ui -- --template react-ts
cd varuna-ui
npm install maplibre-gl @deck.gl/core @deck.gl/layers @deck.gl/mapbox @deck.gl/aggregation-layers recharts zustand
```
- Free basemap, no API key: `https://tiles.openfreemap.org/styles/positron`. For an
  air-gapped demo, download a regional MBTiles pack ahead of time and self-host it.
- Render a MapLibre map centred on the Arabian Sea. Get *something* on screen today.

### Day 2 — the Φ heatmap
- `src/layers/PhiHeatmapLayer.ts` — fetch the mock `.npz`-derived JSON from P1
  (`{lat, lng, weight, time}[]`, downsampled to ~200×200 spatially, 1-hour time bins) and
  render with deck.gl's `HeatmapLayer`. Color ramp: pale yellow → deep red (see the master
  context §15.3 for the exact stops).
- Time slider component scrubbing through the bins. This alone should look like something
  by end of day.

### Day 3 — the backward bloom
- `src/layers/ParticleTripsLayer.ts` — deck.gl `TripsLayer` animating backward particle
  trails, cyan glow, `trailLength: 600`. This is Demo Moment 2 — **let it run a full ten
  seconds, do not speed it up.** Build the `requestAnimationFrame` loop advancing
  `currentTime` at real pace, not compressed.
- `src/layers/VesselTrackLayer.ts` — `PathLayer` for AIS tracks, colored by rank once
  posteriors exist (grey = unscored, gradient by posterior once attribution returns).

### Day 4 — swap to real data + judge controls
- Point all fetches at P4's REST API instead of the mock. Nothing in the layer code should
  need to change if you followed the schema.
- **`src/components/JudgeControls.tsx` — build this now, not later.** Click a vessel on
  the map → toggle its transponder via `POST /cases/{id}/toggle-transponder` → re-render
  the posterior panel and the newly-drawn inferred dark track. Round trip must feel
  instant — pair with P4 on caching if it lags. This is the single highest-leverage 90
  seconds in the entire build.

### Day 5 — suspect panel + landfall clock
- `src/components/SuspectTable.tsx` — ranked vessels with posterior, path-integral,
  emission-prior breakdown (all six published sub-scores — nothing hidden). Latent-source
  row always visible, styled distinctly.
- `src/components/LandfallClock.tsx` — live countdown, `oil reaches {beach} in {H}h {M}m`,
  wired to `ForwardForecast`. Pair with a static "SMS panel" showing mock multilingual
  alerts firing — Section 16.5 says SETU can be entirely mocked.

### Day 6 — evidence + polish
- `src/components/ReliabilityDiagram.tsx` (Recharts) — predicted vs observed frequency,
  the calibration slide, fed by P1's `ece` output. This is the chart no other team will
  have; give it real design attention.
- `src/components/AccuracyVsAge.tsx` — the headline curve, our method vs baselines.
- Transitions between the six demo moments should be one continuous flow, not six
  separate screens. Storyboard with P6.

### Day 7 — failsafe
- **Fallback replay mode**: record a real WebSocket session to JSON, build a player that
  replays it through the identical UI if the live pipeline dies on stage.
- Static screenshot fallback one level below that.
- Final rehearsal pass with P6.

---

## Files You Create

```
varuna-ui/
  src/layers/PhiHeatmapLayer.ts
  src/layers/ParticleTripsLayer.ts
  src/layers/VesselTrackLayer.ts
  src/components/JudgeControls.tsx
  src/components/SuspectTable.tsx
  src/components/LandfallClock.tsx
  src/components/AlertPanel.tsx           (mocked SETU)
  src/components/ReliabilityDiagram.tsx
  src/components/AccuracyVsAge.tsx
  src/components/ReplayPlayer.tsx         (failsafe)
  src/store/caseStore.ts                  (zustand — current Case, selected vessel)
  src/api/client.ts                       (typed fetch wrappers matching P4's routes)
```

## Layer specs (from the master context, do not deviate on the demo-critical two)

```js
new HeatmapLayer({
  id: 'phi-heatmap', getPosition: d => [d.lng, d.lat], getWeight: d => d.weight,
  radiusPixels: 40, intensity: 1.5, threshold: 0.05,
  colorRange: [[255,255,178],[254,204,92],[253,141,60],[240,59,32],[189,0,38]],
});

new TripsLayer({
  id: 'backward-particles', getPath: d => d.path, getTimestamps: d => d.timestamps,
  getColor: [0,200,255], opacity: 0.6, widthMinPixels: 2, trailLength: 600,
  currentTime: animationTime,
});
```

## Interfaces

- **CONSUME:** mock `.npz`→JSON from P1 (day 1), then real REST from P4 (day 4):
  `Case`, `AttributionResult`, `PhiFieldMeta`-derived heatmap JSON, `ForwardForecast`.
- **PRODUCE:** nothing consumed by other subsystems — you are the leaf. Your only export
  is the demo itself.
- **NEED FROM:** P1 by day 1 — mock Φ JSON format frozen. P4 by day 4 — live API up,
  toggle-transponder endpoint fast.

## Claude Code Prompt

```
Read CLAUDE.md and tasks/P5_FRONTEND.md. You are P5, frontend. You own the entire
console: Phi heatmap, backward-bloom particle animation, judge controls, suspect
table, landfall clock, evidence charts, and replay fallback.

Stack is locked: React + Vite + TypeScript, MapLibre GL, deck.gl, Recharts, zustand.
No Leaflet, no Mapbox token.

You are unblocked immediately — P1 is shipping a mock Phi .npz-derived JSON today in
the {lat,lng,weight,time} format described in tasks/P5_FRONTEND.md. Build every layer
against that; swapping in the real API on day 4 should require no rendering-code
changes if the JSON shape matches.

Start now: scaffold the Vite app, install the deck.gl/maplibre stack, and render a
basemap centred on the Arabian Sea using the free OpenFreeMap style URL in the task
file. Get something on screen before doing anything else.
```

## If Claude Is Offline

- deck.gl docs: https://deck.gl/docs — `HeatmapLayer`, `TripsLayer`, `PathLayer`.
- MapLibre + deck.gl overlay pattern: `@deck.gl/mapbox`'s `MapboxOverlay`, added via
  `map.addControl(new MapboxOverlay({layers}))`.
- Free tiles: `https://tiles.openfreemap.org/styles/positron` (no key). Self-host MBTiles
  with `tileserver-gl` for the air-gapped demo.
- Animation loop pattern: increment `animationTime` inside `requestAnimationFrame`,
  call `overlay.setProps({layers: [...]})` each frame — do not re-instantiate layers.
