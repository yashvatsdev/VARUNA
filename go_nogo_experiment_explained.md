# The Go/No-Go Experiment — Explained in Full Detail
## What it is, why it matters, and exactly how to run it

---

## 1. WHAT IS THIS EXPERIMENT?

### The Plain-English Version

Imagine you're investigating a crime. You find footprints at a scene, and you know the wind and rain have been shifting them for the past 24 hours. You want to figure out: **if I reverse the wind and rain effects, can I trace these footprints back to the original spot where the criminal stood — accurately enough to pick them out from a crowd of 20 innocent people who also walked nearby?**

That's exactly what this experiment tests, but with:
- **Footprints** = oil slick on the ocean
- **Wind and rain shifting them** = ocean currents and wind moving the oil
- **Reversing the effects** = running OpenDrift *backward* in time
- **The criminal** = the ship that dumped the oil
- **The crowd of 20 innocent people** = other ships that were sailing in the area

### The Technical One-Liner

> **Can ensemble reverse advection produce an origin probability field Φ that concentrates enough mass on the true release point to distinguish the guilty vessel from N innocent vessels, at operationally realistic slick ages?**

### Why This Must Come First

Your entire project — VARUNA GRID — rests on **one assumption**: that running the drift physics backward produces a *useful* origin field. If that field is so wide and diffuse that every ship in the area scores equally, then:

- NYAYA (attribution) can't rank anyone
- The "calibrated posterior" claim is meaningless
- The "latent dark vessel hypothesis" has nothing to compete against
- The demo moment "backward bloom → posterior resolves" doesn't resolve

**Every hour you spend on NETRA, the frontend, the PPT, or anything else is wasted if this doesn't work.** That's why it's called go/no-go. You need the answer *before* you commit the team.

---

## 2. WHAT YOU NEED

### Software (all free, all `pip install`)

| Package | Purpose | Install |
|---------|---------|---------|
| **OpenDrift** | The drift physics engine — runs particles forward and backward through ocean currents | `pip install opendrift` |
| **NumPy** | All the math — generating tracks, computing path integrals | Already in any Python environment |
| **SciPy** | KDE for building the Φ field from particle positions | `pip install scipy` |
| **matplotlib** | Plotting the results (accuracy curves, Φ heatmaps) | Already in any Python environment |
| **Pandas** | Organising the sweep results | Already in any Python environment |

### Hardware

- **No GPU needed.** This is entirely CPU-based (OpenDrift is a particle advection engine, not deep learning).
- **Any modern laptop** with 4+ cores will do. 8 cores makes the sweep faster (embarrassingly parallel).
- **~2 GB RAM** is plenty.

### Data Downloads

**None required initially.** The first version uses synthetic (made-up) ocean currents. This is deliberate — you want to test the *method*, not the data quality, first.

In Week 2, you upgrade to real CMEMS currents to validate with real physics.

### People

**One person. The lead.** This is a solo experiment. Everyone else works in parallel on their own tasks.

### Time

**5–7 days** for the full sweep with analysis. Day 1–2 is setup and first run; days 3–5 are the parameter sweep; days 6–7 are analysis and decision.

---

## 3. THE EXPERIMENT, STEP BY STEP

Here's exactly what you do, broken into 6 phases:

---

### PHASE 1: Create a Fake Ocean (Day 1, ~2 hours)

You need an ocean current field to drive the drift physics. For the first pass, **make one up** — a uniform current with some rotation to simulate a realistic flow.

```
What you're building:
- A 200 km × 200 km patch of ocean
- Surface current: 0.3 m/s, direction rotating ±15° over 48 hours
- Wind: 8 m/s from the west, varying ±3 m/s over time
```

**Why synthetic first?** Because if the method fails even on *perfect, known* currents, it will definitely fail on noisy real currents. Synthetic is the easy test. If it passes here, you test with real data. If it fails here, you know the method itself is broken.

```python
# Pseudocode — Phase 1
from opendrift.readers import reader_oscillating  # or create a custom reader

# Option 1: Use OpenDrift's built-in constant/oscillating readers
# Option 2: Create a small NetCDF file with synthetic current data

# The current field should be:
# - Spatially uniform (same speed everywhere) — simplest case
# - Temporally varying (direction rotates slowly) — adds realism
# - Covers at least 200×200 km and 72 hours
```

OpenDrift has built-in "constant" and "basemap" readers that can serve as synthetic forcing without writing any NetCDF files. Start with `reader_current_from_track` or simply set a constant fallback:

```python
from opendrift.models.oceandrift import OceanDrift
o = OceanDrift(loglevel=50)  # suppress logs

# Set constant fallback values (simplest synthetic ocean)
o.set_config('environment:fallback:x_sea_water_velocity', 0.25)  # m/s east
o.set_config('environment:fallback:y_sea_water_velocity', 0.10)  # m/s north
o.set_config('environment:fallback:x_wind', -6.0)  # m/s
o.set_config('environment:fallback:y_wind', 2.0)   # m/s
```

---

### PHASE 2: Simulate the "Crime" — Forward Drift (Day 1, ~1 hour)

Now simulate what actually happens when a ship dumps oil:

```
1. Pick a RELEASE POINT: lat=15.0°N, lon=72.0°E (arbitrary — somewhere in the Arabian Sea)
2. Pick a RELEASE TIME: T₀ = 00:00 UTC on some date
3. Seed 1,000 particles at the release point at time T₀
4. Run OpenDrift FORWARD for 24 hours (simulating the oil drifting)
5. At T₀ + 24h, capture the POSITIONS of all 1,000 particles
```

The particles at T₀ + 24h represent **the oil slick as a satellite would see it** — spread out, deformed, moved away from the release point.

```python
from datetime import datetime, timedelta

release_point = (72.0, 15.0)  # lon, lat
release_time = datetime(2025, 6, 15, 0, 0)  # arbitrary date

# Seed particles at the release point
o.seed_elements(
    lon=release_point[0], lat=release_point[1],
    number=1000,
    time=release_time,
    radius=500  # 500m spread to simulate a discharge, not a point
)

# Run FORWARD 24 hours
o.run(
    duration=timedelta(hours=24),
    time_step=900  # 15 minutes, POSITIVE = forward
)

# The final positions of all particles = "the observed slick"
final_lons = o.history['lon'][:, -1]
final_lats = o.history['lat'][:, -1]
observation_time = release_time + timedelta(hours=24)
```

**What you now have:** 1,000 particle positions that represent an oil slick 24 hours old. You know the **true** release point (72.0°E, 15.0°N) and the **true** release time (T₀). The system you're testing does NOT know these — it only sees the slick positions.

---

### PHASE 3: Run the Backward Ensemble (Day 1–2, ~2 hours)

This is **the core of VARUNA's mechanism**. You take the observed slick and run the physics *in reverse* to estimate where the oil came from.

```
1. Seed N particles at the OBSERVED slick positions (the output of Phase 2)
2. Run OpenDrift BACKWARD for 24+ hours
3. BUT: run it M times, each with SLIGHTLY DIFFERENT physics parameters
   (this is the "ensemble" — it captures uncertainty)
4. Collect all the backward particle positions at each timestep
5. Build the origin probability field Φ(x, y, t) from the particle density
```

**The ensemble perturbation is the key innovation.** Each of the M runs uses slightly different:
- **Wind-drift coefficient** (how much wind pushes the oil): normally 3%, but perturb between 2% and 4%
- **Horizontal diffusivity** (how much the oil spreads randomly): perturb between 5 and 50 m²/s
- **Current field noise** (add ±20% error to current speeds, ±15° to directions)

```python
import numpy as np
from scipy.stats import gaussian_kde

M = 30  # number of ensemble members
N = 500  # particles per member
all_backward_positions = []  # collect all (lon, lat, time) tuples

for m in range(M):
    o_back = OceanDrift(loglevel=50)

    # PERTURB the physics for this ensemble member
    wind_drift_factor = np.random.uniform(0.02, 0.04)  # 2-4%
    diffusivity = np.random.uniform(5, 50)  # m²/s

    o_back.set_config('drift:wind_drift_factor', wind_drift_factor)
    o_back.set_config('drift:horizontal_diffusivity', diffusivity)

    # Same constant currents (or add noise to these too)
    current_noise = np.random.uniform(0.8, 1.2)  # ±20%
    o_back.set_config('environment:fallback:x_sea_water_velocity', 0.25 * current_noise)
    o_back.set_config('environment:fallback:y_sea_water_velocity', 0.10 * current_noise)

    # Seed at the OBSERVED slick positions
    # (subsample if N < number of forward particles)
    indices = np.random.choice(len(final_lons), N, replace=False)
    o_back.seed_elements(
        lon=final_lons[indices],
        lat=final_lats[indices],
        number=N,
        time=observation_time
    )

    # Run BACKWARD (negative time step!)
    o_back.run(
        duration=timedelta(hours=30),  # go back a bit further than 24h
        time_step=-900  # NEGATIVE = backward, 15-minute steps
    )

    # Collect positions at each timestep
    for t_idx in range(o_back.history['lon'].shape[1]):
        lons = o_back.history['lon'][:, t_idx]
        lats = o_back.history['lat'][:, t_idx]
        time = observation_time - timedelta(seconds=900 * t_idx)
        for i in range(len(lons)):
            all_backward_positions.append((lons[i], lats[i], time.timestamp()))

# Now all_backward_positions contains N×M×T points
# representing WHERE the oil MIGHT have come from, at EACH past time
```

### PHASE 4: Build the Origin Probability Field Φ(x, y, t) (Day 2, ~1 hour)

The Φ field answers: **"At each point in space and time, how likely is it that the oil was released here?"**

You build it by computing the **density** of backward particles at each location and time.

```
Φ(x, y, t) = density of backward ensemble particles at position (x,y) at time t
```

The places where many backward particles from many ensemble members converge = high-probability origin locations.

```python
# Discretise time into 1-hour bins
# For each time bin, compute a 2D kernel density estimate (KDE)

time_bins = np.arange(
    observation_time.timestamp() - 30*3600,  # 30 hours back
    observation_time.timestamp(),
    3600  # 1-hour bins
)

phi_field = {}  # {time_bin: 2D KDE function}

for t_bin in time_bins:
    # Get all particles in this time window
    pts = [(lon, lat) for lon, lat, t in all_backward_positions
           if t_bin <= t < t_bin + 3600]

    if len(pts) < 10:
        continue

    pts = np.array(pts)
    kde = gaussian_kde(pts.T, bw_method=0.05)  # bandwidth tuning matters
    phi_field[t_bin] = kde

# Φ is now a collection of KDEs, one per time bin
# To evaluate: phi_field[t_bin]([lon, lat]) → probability density
```

**What Φ looks like visually:** A glowing heat blob on the map. At recent times (close to observation), it's wide (the slick is still spread). As you go further back in time, it should **converge** toward the true release point — like rewinding a video of ink spreading in water.

---

### PHASE 5: Generate Vessel Tracks and Score Them (Day 2–3, ~2 hours)

Now create synthetic "ships" — some innocent, one guilty — and see if your Φ field can tell them apart.

```
1. Create K vessel tracks (straight lines, curves, loitering patterns)
2. ONE of them (the "guilty" vessel) passes through the TRUE release point at time T₀
3. The others are "innocent" — they sail nearby but NOT through the release point
4. For each vessel, compute its PATH-INTEGRAL LIKELIHOOD through Φ
```

**The path integral** is the key scoring mechanism. For each vessel k with trajectory `(x_k(t), y_k(t))`:

```
L_k = ∫ Φ(x_k(t), y_k(t), t) dt
```

In plain English: **walk along the vessel's track through space and time, and at each point, ask "how much origin probability is here?" Add it all up.** The vessel whose track accumulated the most Φ-mass is the most likely culprit.

```python
def generate_vessel_track(start_lon, start_lat, speed_knots, heading_deg,
                          start_time, duration_hours, n_points=100):
    """Generate a simple straight-line vessel track."""
    times = [start_time + timedelta(hours=h)
             for h in np.linspace(0, duration_hours, n_points)]
    speed_ms = speed_knots * 0.5144  # knots to m/s

    heading_rad = np.radians(heading_deg)
    dx = speed_ms * np.sin(heading_rad)  # m/s east
    dy = speed_ms * np.cos(heading_rad)  # m/s north

    lons, lats = [start_lon], [start_lat]
    for i in range(1, n_points):
        dt = (times[i] - times[i-1]).total_seconds()
        # Approximate: 1° lon ≈ 111km × cos(lat), 1° lat ≈ 111km
        new_lon = lons[-1] + (dx * dt) / (111000 * np.cos(np.radians(lats[-1])))
        new_lat = lats[-1] + (dy * dt) / 111000
        lons.append(new_lon)
        lats.append(new_lat)

    return list(zip(lons, lats, [t.timestamp() for t in times]))


def compute_path_integral(track, phi_field, time_bins):
    """Score a vessel track against the Φ field."""
    score = 0.0
    for lon, lat, t in track:
        # Find the right time bin
        t_bin = None
        for tb in time_bins:
            if tb <= t < tb + 3600:
                t_bin = tb
                break
        if t_bin is None or t_bin not in phi_field:
            continue

        # Evaluate Φ at this vessel's position and time
        density = phi_field[t_bin]([[lon], [lat]])[0]
        score += density

    return score


# === Generate vessels ===
K = 20  # total vessels (1 guilty + 19 innocent)
vessels = []

# GUILTY vessel: passes through the true release point at T₀
guilty_track = generate_vessel_track(
    start_lon=71.8, start_lat=14.8,  # starts SW of release point
    speed_knots=12, heading_deg=30,   # heading NE
    start_time=release_time - timedelta(hours=6),
    duration_hours=12
)
# Verify it passes near (72.0, 15.0) around release_time
vessels.append(('guilty', guilty_track))

# INNOCENT vessels: various tracks that DON'T pass through the release point
for i in range(K - 1):
    start_lon = np.random.uniform(71.5, 72.5)
    start_lat = np.random.uniform(14.5, 15.5)
    heading = np.random.uniform(0, 360)
    speed = np.random.uniform(8, 18)

    track = generate_vessel_track(
        start_lon=start_lon, start_lat=start_lat,
        speed_knots=speed, heading_deg=heading,
        start_time=release_time - timedelta(hours=np.random.uniform(2, 12)),
        duration_hours=np.random.uniform(8, 24)
    )
    vessels.append((f'innocent_{i}', track))

# === Score all vessels ===
scores = {}
for name, track in vessels:
    scores[name] = compute_path_integral(track, phi_field, time_bins)

# === Who does the system think did it? ===
ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
top_1 = ranked[0][0]  # highest-scoring vessel

print(f"System says: {top_1}")
print(f"Truth: guilty")
print(f"Correct: {top_1 == 'guilty'}")
```

---

### PHASE 6: Sweep the Parameter Grid (Day 3–5)

Now repeat Phases 2–5 **hundreds of times** with different settings:

```
┌─────────────────────────────────────────────────────────────┐
│                    THE SWEEP GRID                            │
├──────────────────┬──────────────────────────────────────────┤
│ SLICK AGE (T)    │  2h,  6h,  12h,  24h,  48h              │
│                  │  (how long the oil has been drifting)     │
├──────────────────┼──────────────────────────────────────────┤
│ TRAFFIC DENSITY  │  5,  10,  20,  50  vessels               │
│ (K)              │  (how many ships are in the area)         │
├──────────────────┼──────────────────────────────────────────┤
│ FORCING ERROR    │  low (±5%), medium (±20%), high (±40%)   │
│ (ε)              │  (how wrong are the currents/wind)        │
├──────────────────┼──────────────────────────────────────────┤
│ TOTAL CELLS      │  5 × 4 × 3 = 60 parameter combinations  │
│ TRIALS PER CELL  │  50–100 Monte Carlo repetitions           │
│ TOTAL RUNS       │  3,000–6,000 simulations                  │
└──────────────────┴──────────────────────────────────────────┘
```

For each cell, record:
- **Top-1 accuracy**: did the highest-scoring vessel = the guilty one?
- **Top-3 accuracy**: was the guilty vessel in the top 3?
- **Baseline comparison**: what if you just picked the nearest vessel to the slick? (This is the "dumb" baseline)

```python
results = []

for slick_age_hours in [2, 6, 12, 24, 48]:
    for num_vessels in [5, 10, 20, 50]:
        for forcing_error in ['low', 'medium', 'high']:
            for trial in range(100):

                # 1. Forward drift (Phase 2) with this slick_age
                # 2. Backward ensemble (Phase 3) with this forcing_error
                # 3. Build Φ (Phase 4)
                # 4. Generate & score num_vessels tracks (Phase 5)
                # 5. Record whether top-1 and top-3 are correct

                results.append({
                    'slick_age': slick_age_hours,
                    'num_vessels': num_vessels,
                    'forcing_error': forcing_error,
                    'trial': trial,
                    'top1_correct': top_1 == 'guilty',
                    'top3_correct': 'guilty' in [r[0] for r in ranked[:3]],
                    'baseline_correct': nearest_vessel == 'guilty',
                })
```

---

## 4. WHAT THE RESULTS LOOK LIKE

### SUCCESS (GO ✅)

You produce a plot like this:

```
Top-1 Attribution Accuracy vs Slick Age
(20 vessels, medium forcing error)

100% ┤
     │  ●─────●               ← VARUNA (your method)
 80% ┤         ╲
     │          ╲
 60% ┤           ●─────●
     │                  ╲
 40% ┤  ○───○             ●
     │       ╲
 20% ┤        ○────○────○     ← Nearest-vessel baseline
     │
  0% ┤
     └──┬──┬───┬───┬───┬──
        2h  6h  12h 24h 48h
              Slick Age
```

**What "go" looks like:**
- At **2h**: both methods work (~90%+). The slick hasn't moved far, so even "nearest ship" is right.
- At **6–12h**: the baseline starts failing. Your method holds. **This is the gap opening.**
- At **24h**: your method is at ~50–70%. Baseline is at ~15–25%. **This is the operational sweet spot for India.**
- At **48h**: your method degrades too, but still above baseline. You acknowledge this honestly.

The key number: **top-1 accuracy at 24h with 20 vessels ≥ 50%.** If you hit this, the method works.

### FAILURE (NO-GO ❌)

```
Top-1 Attribution Accuracy vs Slick Age
(20 vessels, medium forcing error)

100% ┤
     │  ●─────●
 80% ┤         ╲
     │
 60% ┤
     │
 40% ┤           ●
     │  ○───○
 20% ┤       ○────●────●──●   ← Both methods crash together
     │            ○────○──○
  0% ┤
     └──┬──┬───┬───┬───┬──
        2h  6h  12h 24h 48h
```

**What "no-go" looks like:**
- Your method is barely better than the baseline at any age
- At 24h, both are below 30% — essentially guessing
- The Φ field is so wide that every track intersects it equally
- **The posterior is flat** — no discrimination

---

## 5. THE DECISION CRITERIA

| Result at 24h / 20 vessels | Decision | Action |
|---------------------------|----------|--------|
| **Top-1 ≥ 60%** and clear separation from baseline | **Strong GO** ✅ | Full speed ahead. This is a publishable result. |
| **Top-1 = 40–60%** and better than baseline | **Conditional GO** ⚠️ | Proceed, but invest in emission priors (vessel type, AIS gaps) to boost discrimination |
| **Top-1 = 25–40%** | **Weak — try fixes first** | Spend 2 more days: sharpen age prior, increase M, add emission priors. Re-sweep. |
| **Top-1 < 25%** or indistinguishable from baseline | **NO-GO** ❌ | Pivot to "Attribution-Aware Detection" (see fallback plan in the roadmap) |

---

## 6. WHAT EACH PARAMETER TESTS

| Parameter | What it means physically | What it tells you |
|-----------|-------------------------|-------------------|
| **Slick age (T)** | How many hours since the oil was dumped. Longer = oil has drifted further = harder to trace back. | **Your system's useful operational range.** India's default is 12–48h (sparse satellite revisit). |
| **Traffic density (K)** | How many ships are in the area. More ships = more candidates = harder to pick the right one. | **Whether the posterior is genuinely discriminative** or just picks any ship near the origin field. |
| **Forcing error (ε)** | How wrong are your current/wind data compared to reality. Real CMEMS has ~20% error at 1/12° resolution. | **The floor the physics sets** — no algorithm can be better than the data allows. This tells you if ~8 km resolution currents are sufficient. |

---

## 7. COMMON PITFALLS AND TIPS

> [!WARNING]
> **Use `OceanDrift`, NOT `OpenOil`, for backtracking.** OpenOil includes weathering processes (evaporation, emulsification) that are physically irreversible — running them backward produces nonsense. For backward tracing, you only need the *trajectory* (advection by currents + wind drift), which `OceanDrift` handles perfectly.

> [!TIP]
> **Start with the simplest possible setup.** Constant currents, straight-line vessel tracks, 5 vessels, 6-hour slick age. Get ONE successful run before scaling up. Debug your Φ-building and path-integral code on this easy case first.

> [!TIP]
> **Visualise Φ at every step.** Plot the backward particle positions as a scatter plot overlaid on the vessel tracks. You should visually see the particles converging toward the release point. If they're scattered everywhere, something is wrong with the backward run.

> [!IMPORTANT]
> **The baseline must be honest.** The "nearest vessel" baseline means: at observation time, which vessel is closest to the centroid of the slick? This is roughly what existing tools (Cerulean) do. If your method can't beat this trivial heuristic, the entire RDPA concept doesn't add value.

---

## 8. CHECKLIST — WHAT YOU NEED TO START TODAY

- [ ] Python 3.10+ environment
- [ ] `pip install opendrift numpy scipy matplotlib pandas`
- [ ] Run OpenDrift's "back and forth" example to verify backward simulation works
- [ ] A text editor / Jupyter notebook
- [ ] ~4–6 hours of focused coding time for Phase 1–5 (first successful run)
- [ ] ~2–3 days of compute time for the full sweep (can run overnight)
- [ ] **No GPU. No SAR imagery. No downloaded datasets. No API keys.**

This experiment is pure simulation. It answers the most important question in the project using nothing but math and a laptop.

---

*Go/No-Go Experiment Guide · VARUNA GRID · SIH 2026*
