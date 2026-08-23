# ML_TRAINING_GUIDE.md
## VARUNA GRID v2 — standalone training manual

Covers NETRA (segmentation + look-alike rejection), the age model, CHHAYA (dark-vessel
detection), the behavioural prior, calibration, and OOD detection.

> **Commands marked 🔧 reference scripts that do not exist yet.** They are the specification
> for what ROLE 01 builds. Commands marked ✅ work today. Nothing here invents a dataset path.

---

## 0. Scope — what is ML and what deliberately is not

| Subproblem | Approach | Why |
|---|---|---|
| Slick segmentation | **U-Net (ML)** | Texture and context, not intensity alone |
| Look-alike rejection | **Multi-class head + ERA5 wind channel (ML)** | Low-wind look-alikes are identifiable from physical context the image lacks |
| Slick age | **Small regressor → a DISTRIBUTION (ML)** | PS says "if feasible". The ensemble consumes the distribution |
| Dark-vessel detection | **xView3 pretrained (ML)** | Solved problem, open weights. Do not reinvent |
| Backward drift | **NOT ML — OpenDrift** | Physics is known and trusted. Learning it destroys auditability |
| Attribution scoring | **NOT ML — path integral** | A learned ranker needs labels that do not exist |
| Behavioural prior | **Rules + gradient boosting** | Interpretable features beat a black box a defence lawyer will attack |
| Calibration | **Isotonic regression** | Turns a score into a probability that means something |

**No RL anywhere in the core.** No online learning anywhere at all.

---

## 1. NETRA — slick segmentation + look-alike rejection

### 1.1 Datasets

| Dataset | Content | Size | Access |
|---|---|---|---|
| Zenodo Sentinel-1 Oil Spill I | 1,200 images + masks, 2048×2048×2 (VV+VH) | ~41 GB | [8346860](https://zenodo.org/records/8346860) CC-BY-4.0 |
| Zenodo II (val) | validation split | — | [8253899](https://zenodo.org/records/8253899) |
| Zenodo III (test) | test split | — | [13761290](https://zenodo.org/records/13761290) |
| **ESSD 2025 look-alikes** | 3,225 oil objects / 1,365 patches + **2,290 look-alike patches** | ~5 GB | [PANGAEA.980773](https://doi.org/10.1594/PANGAEA.980773) CC-BY-4.0 |
| Krestenitis / MKLab | 5 classes (oil, look-alike, land, ship, sea) | ~400 MB | Application required |

The **ESSD look-alike set is the single most valuable asset** — it is what lets the network
learn rejection rather than "dark patch = oil".

### 1.2 Ingestion

Zenodo tiles are 2048×2048 → cut into sixteen 512×512 tiles. Discard tiles with <1% oil
unless deliberately retained as negatives. Target an oil : look-alike ratio near **1:2**.

Channels — **3, not 2**:

```
ch0  VV  (σ⁰, dB, normalised)
ch1  VH  (σ⁰, dB, normalised)
ch2  ERA5 10 m wind speed, interpolated to the tile grid
```

Feeding wind into the network is the cheapest large win available: low-wind look-alikes are
the dominant false-positive source and are physically identifiable from context the image
alone does not contain.

### 1.3 Splits — the part that decides whether the numbers mean anything

- **Geographic split.** Hold out entire regions, never random tiles. Tiles from one scene
  share speckle statistics, wind state, and often the same slick — a random split leaks and
  inflates IoU by a wide margin.
- **Temporal split.** Test dates strictly after train dates.
- **Never** let two tiles from the same scene land in different splits.

Record the split manifest under `data/manifests/` and hash it into the model card.

### 1.4 Architecture

```python
import segmentation_models_pytorch as smp

model = smp.Unet(
    encoder_name="resnet34",       # matches Cerulean's published backbone → fair comparison
    encoder_weights="imagenet",
    in_channels=3,                 # VV, VH, wind
    classes=3,                     # background / oil / look_alike
)
```

Plus a pooled per-tile confidence head for triage.

### 1.5 Training recipe

| Setting | Value | Note |
|---|---|---|
| Loss | `0.5·Dice + 0.5·CrossEntropy` | inverse-frequency class weights — oil is rare |
| Optimizer | AdamW, lr 3e-4, wd 1e-4 | |
| Schedule | Cosine annealing, 5-epoch warmup | |
| Batch | 8 @ 512² (16 GB VRAM) | halve for 8 GB |
| AMP | on (`torch.amp.autocast`) | ~2× throughput |
| Epochs | 40–60, early stop patience 8 on val IoU | |
| Augmentation | flips, 90° rotations, **speckle noise** | |
| **Never** | brightness/contrast jitter | destroys the σ⁰ physics the model must learn |
| Seed | fixed, recorded | reproducibility is a contract requirement |

### 1.6 Commands

```bash
🔧 python -m varuna_netra.train \
     --config configs/netra_resnet34.yaml \
     --data-manifest data/manifests/netra_geo_split_v1.json \
     --epochs 50 --batch-size 8 --amp --seed 42 \
     --mlflow-uri http://localhost:5000

🔧 python -m varuna_netra.evaluate --checkpoint models/netra/best.pt --split test
🔧 python -m varuna_netra.export   --checkpoint models/netra/best.pt \
     --out models/netra/netra_unet.torchscript
```

### 1.7 Evaluation — report these separately

| Metric | Why |
|---|---|
| IoU / F1 on the oil class | Headline segmentation quality |
| **False-positive rate on the ESSD look-alike set** | **Reported separately.** This is the number that shows we understood the real problem — a model with great IoU and a 40% look-alike FP rate is operationally useless |
| Per-region breakdown | Reveals geographic overfitting |
| Wind-channel ablation | Expect the gain to appear almost entirely in low-wind cases — say exactly that |
| OOD score distribution | See §5 |

Publish the failure cases. Showing where it breaks earns more credibility than hiding it.

---

## 2. Age model — a distribution, never a point

The PS says "age if feasible". It is weakly identifiable, and pretending otherwise
poisons everything downstream: PRATIVARTAN integrates over the age prior, so a
falsely-confident age produces a falsely-tight origin field.

**Output:** log-normal parameters `(age_prior_mean_hours, age_prior_std_hours)`.

**Features:** area, perimeter, elongation, fractal dimension, mean/var of σ⁰ contrast,
integrated wind history over the plausible window, spreading ratio.

**Model:** gradient boosting with a quantile or NLL objective, or a small MLP with a
Gaussian NLL head. Calibrate the interval — a 90% interval must contain truth ~90% of the
time on held-out simulated cases.

**Training data:** the simulation harness (`experiments/`), where true age is known by
construction.

**Rule:** when the signal is weak, **widen the prior**. Degrade honestly. PRATIVARTAN
reports `age_sensitivity`; if it dominates, the UI says the origin is driven by the age
assumption rather than the data.

---

## 3. CHHAYA — dark-vessel detection

Use the **AllenAI xView3 reference model and weights** —
[`github.com/allenai/sar_vessel_detect`](https://github.com/allenai/sar_vessel_detect).
Pretrained inference first; fine-tune only if measured recall is inadequate on our scenes.

**The critical logic is not the detector — it is the finding.** Distinguish:

| `LatentFinding` | Means |
|---|---|
| `NO_PLAUSIBLE_VISIBLE_SOURCE` | Good coverage, no candidate explains Φ |
| `VISIBLE_SOURCES_EXIST_BUT_WEAK` | Candidates exist, all score poorly |
| `RADAR_CONTACT_WITHOUT_AIS` | A detected object with no matching AIS |
| `INSUFFICIENT_COVERAGE` | **Cannot conclude either way** |

Never infer "dark vessel" from absence of AIS alone. A ship outside the scene footprint,
or an AIS latency gap, produces the same absence. That conflation is threat A-05.

---

## 4. Behavioural prior (emission prior π_k)

Six features, all interpretable, **weights published in the UI**:

```
gap_score        fraction of the window with AIS gaps > 30 min
speed_anomaly    deviation from type-expected speed
loiter_score     time < 3 kt within 5 nm of a point
night_proximity  near the origin field between 00:00–05:00 local
type_weight      tanker/cargo vs passenger/fishing
combined         the π_k actually multiplied into the likelihood
```

Start hand-tuned and publish the table. Move to XGBoost only when the simulation harness
has enough labelled cases — and even then, keep the feature set interpretable. A defence
lawyer can attack a black box; they cannot attack six disclosed numbers.

**Report prior and evidence contributions separately** so a reviewer can see when the prior
is doing the work (threat N-05).

---

## 5. OOD detection

NETRA must know when a scene is unlike anything it trained on.

- Energy-based score or max-softmax-probability on the segmentation logits
- Mahalanobis distance in encoder feature space against training-set statistics
- Threshold set at the 95th percentile of the training distribution

High OOD → `quality.ood_score` high → trust downgraded → validity gate may restrict.
Ship a low-tech version (feature-space Mahalanobis) rather than nothing.

---

## 6. Calibration

**Blocked until the go/no-go harness is valid** (threat N-06). Fitting isotonic regression
on an invalid sweep produces a confidently wrong probability, which is worse than an
uncalibrated score.

Once valid:

```python
from sklearn.isotonic import IsotonicRegression
iso = IsotonicRegression(out_of_bounds="clip")
iso.fit(raw_posteriors, was_correct)     # from the rebuilt simulation sweep
```

**Report:**
- **ECE** — 10 bins, `Σ (n_b/N)·|acc_b − conf_b|`. Target < 0.05.
- **Reliability diagram** — predicted vs observed frequency. If it sits near the diagonal,
  the argument is won. No competing team will show this.
- **OOD guard** — inputs outside the fit domain set `calibration_state=OUT_OF_DOMAIN`, and
  the UI presents the numbers as a ranking, not as probabilities.

**Honesty:** calibration is valid *given the physics model*. If CMEMS systematically
misaligns with real conditions, the calibration inherits that bias. State this in the model
card and the evidence manifest.

---

## 7. Experiment tracking and versioning

MLflow (`docker compose --profile mlops up`). Log for every run: git SHA, config, data
manifest hash, seed, all metrics, the split definition, and the artifact.

**Every model version stamped on every inference output** (`model_version` in the
`EvidenceEnvelope`) — unregistered versions must be rejected at load (threat G-08).

Promotion path: `staging → validated → production`, with a human approving each step.

---

## 8. Reproducibility checklist

- [ ] Seeds fixed and recorded (`torch`, `numpy`, `random`, CUDA determinism where feasible)
- [ ] Data manifest hashed and committed
- [ ] Config committed, not passed ad hoc
- [ ] Git SHA logged in MLflow
- [ ] Environment pinned (`pyproject.toml` + lock)
- [ ] Re-running the command reproduces metrics within a stated tolerance
- [ ] Model card written before promotion

---

## 9. Model cards (required before promotion)

`models/<name>/MODEL_CARD.md` must state: intended use · training data with split strategy ·
metrics **including look-alike FP rate** · known failure modes · OOD behaviour ·
calibration validity domain · **limitations** · ethical considerations (this model
contributes to an enforcement recommendation and must never be the sole basis for naming a
vessel).

---

## 10. Known failure cases to document, not hide

| Case | Behaviour |
|---|---|
| Low wind (< 3 m/s) | Look-alike FP rate rises sharply — wind gate downgrades confidence |
| Algal blooms | Persistent seasonal FPs — SMRITI corridor memory helps |
| Natural seeps | Recurring same-location dark patches, no vessel correlation — flag as natural |
| Rain cells | Transient dark patches — temporal context needed |
| Very thin sheens | Below detection threshold; report as coverage limit |
| Land contamination | Coastline mask; flag geolocation confidence |
| Ambiguous age | Widen the prior; `age_sensitivity` surfaces the consequence |
