# P2 — ML / VISION
## Owns: NETRA (M2, M3) · CHHAYA (M9b)

Detection is not our innovation — an *adequate* detector is sufficient, a perfect one is
not required. But look-alike rejection **is** the hardest perception problem in this PS,
and the wind channel is the cheapest large win available. Read `CLAUDE.md` first.

---

## Day-by-Day

### Day 1 — data
- Download Zenodo Parts I–III (~45 GB, start immediately — it takes hours):
  `zenodo.org/records/8346860`, `/8253899`, `/13761290`.
- Download the ESSD Eastern Mediterranean look-alike set: `doi.org/10.1594/PANGAEA.980773`.
  3,225 oil objects + **2,290 look-alike patches** — the most valuable data we have.
- `src/netra/dataset.py` — a `torch.utils.data.Dataset` yielding
  `(3, 512, 512)` float32 tiles and `(512, 512)` int64 masks.
  Channels: **VV, VH, ERA5 10 m wind speed** (broadcast constant per tile until P3's real
  wind grids land on day 3; then interpolate properly).

### Day 2 — training
- `src/netra/model.py` — exact architecture:
  ```python
  smp.Unet(encoder_name="resnet34", encoder_weights="imagenet",
           in_channels=3, classes=3)   # background / oil / look_alike
  ```
  ResNet34 matches Cerulean's published backbone, which makes the comparison fair and
  defensible. Two outputs from one decoder: per-pixel class, plus a pooled per-tile
  confidence head.
- `src/netra/train.py` — loss `0.5·Dice + 0.5·CrossEntropy`, class weights inversely
  proportional to pixel frequency (oil is rare). AdamW, lr 3e-4, cosine schedule, batch 8
  at 512², AMP on. Augment: flips, 90° rotations, and speckle noise — **never** brightness
  jitter, which destroys the σ⁰ physics.
- Train on Colab Pro / Kaggle P100 (4–8 h). Checkpoint every epoch to Drive.

### Day 3 — evaluate honestly
- `src/netra/evaluate.py` — IoU and F1 on the Zenodo test split, and **the false-positive
  rate on the ESSD look-alike set reported separately.** That second number is the one
  that shows we understood the real problem. Report it even when it is bad.
- Ablation for P1's table: with vs without the wind channel. Expect the gain to appear
  almost entirely on low-wind look-alikes — say exactly that.

### Day 4 — characterisation + export
- `src/netra/characterise.py` (M3) — from the mask: `area_km2`, `perimeter_km`,
  `elongation` (major/minor axis of the fitted ellipse), `orientation_deg`.
- **Age prior — a distribution, never a point** (Section 11). Log-normal parameterised by
  spreading ratio and elongation: a thin, wide, diffuse slick is older and *less certain*.
  Output `age_prior_mean_hours` and `age_prior_std_hours`. When the signal is weak, widen
  the prior — degrade honestly rather than guessing.
- `src/netra/export.py` — TorchScript trace to `models/netra_unet.torchscript`. Do this on
  day 4, not the night before travel.

### Day 5 — inference wrapper
- `src/netra/inference.py` — `detect(scene_path, wind_grid, obs_time) -> list[SlickDetection]`.
  Overlapping 512² tiles, stride 256, average the logits on overlap, threshold, connected
  components, drop blobs under ~0.5 km², emit one `SlickDetection` each.
- Wind gate: if mean wind < `NETRA_WIND_GATE_MS`, downgrade confidence and set
  `look_alike_type=LOW_WIND`. Physics the network cannot see from pixels alone.

### Day 6 — CHHAYA
- `src/chhaya/detector.py` — wrap AllenAI's xView3 reference model
  (`github.com/allenai/sar_vessel_detect`). **Pretrained weights, no training.**
- `src/chhaya/match.py` — cross-reference detections against AIS positions at scene time.
  Unmatched object > 30 m within 50 km of the slick → `DarkVesselDetection(is_dark=True)`.
  This is what gives P1's latent hypothesis a face on screen.

### Day 7 — demo support
- Run NETRA + CHHAYA over all demo scenes, cache outputs as JSON so `DEMO_MODE` never
  needs the GPU. Tune thresholds per case with P6. Hand P1 a real `SlickDetection`.

---

## Files You Create

| Path | Purpose |
|---|---|
| `src/netra/dataset.py` | Zenodo + ESSD loader, 3-channel tiles |
| `src/netra/model.py` | U-Net ResNet34, 3 in / 3 classes + confidence head |
| `src/netra/train.py` | Training loop, Dice+CE, AMP |
| `src/netra/evaluate.py` | IoU, F1, **separate look-alike FP rate** |
| `src/netra/characterise.py` | M3 morphometry + log-normal age prior |
| `src/netra/inference.py` | Tiled inference → `list[SlickDetection]` |
| `src/netra/export.py` | TorchScript export |
| `src/chhaya/detector.py` | xView3 wrapper |
| `src/chhaya/match.py` | AIS cross-reference → `DarkVesselDetection` |

## Interfaces

- **PRODUCE:** `SlickDetection` (→ P3 and P1), `DarkVesselDetection` (→ P1).
- **CONSUME:** SAR scenes and ERA5 wind grids (P3/P6), AIS positions for matching (P4).
- **NEED FROM:** P3 by day 3 — ERA5 wind on the scene grid. P6 by day 6 — the frozen demo
  scene list. P4 by day 6 — AIS positions at scene time for CHHAYA matching.

## Claude Code Prompt

```
Read CLAUDE.md and tasks/P2_ML_VISION.md. You are P2, ML/vision. You own NETRA
(slick segmentation + look-alike rejection + characterisation) and CHHAYA (xView3
dark-vessel detection).

Import all shared types from src.common.schemas — especially SlickDetection and
DarkVesselDetection. Do not redefine them. Python 3.10+, type hints, no tutorial
comments.

Architecture is fixed: smp.Unet(encoder_name="resnet34", encoder_weights="imagenet",
in_channels=3, classes=3). Channels are VV, VH, ERA5 10m wind speed. Loss is
0.5*Dice + 0.5*CrossEntropy with inverse-frequency class weights.

Start with src/netra/dataset.py now — the Zenodo + ESSD loader producing (3,512,512)
float32 tiles and (512,512) int64 masks with classes background/oil/look_alike.
```

## If Claude Is Offline

- `segmentation_models_pytorch` docs: https://smp.readthedocs.io
- Dice loss: `1 - 2·|X∩Y| / (|X|+|Y|)`, computed per class, averaged, background excluded.
- Zenodo tiles are 2048×2048×2 — cut into sixteen 512² tiles, discard tiles with < 1% oil
  unless kept deliberately as negatives.
- ESSD patches are the look-alike source; label them class 2 and keep the oil/look-alike
  ratio near 1:2 so the network actually learns rejection.
- xView3 reference model + weights: https://github.com/allenai/sar_vessel_detect
- Ellipse fit for elongation: `cv2.fitEllipse` on the largest contour → `major/minor`.
