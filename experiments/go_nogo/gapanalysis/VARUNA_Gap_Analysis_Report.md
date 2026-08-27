# VARUNA — Research & Technology Gap Analysis
SIH 2026 / SIH26143

---

## 1. Executive summary

VARUNA is a multimodal marine-pollution intelligence pipeline combining Sentinel-1 SAR slick detection, look-alike rejection, AIS vessel trajectories, dark-vessel SAR detections, and environmental drift/backtracking. The uploaded project guide assigns these roles to NETRA, NYAYA, CHHAYA and PRATIVARTAN/PRAVAAH. The evidence shows that the individual components are not novel: Sentinel-1 oil-slick detection, SAR vessel detection, AIS association and drift modelling already exist. The defensible gap is rigorous integration into uncertainty-aware source attribution under slick-age growth, AIS gaps/false broadcasts, environmental uncertainty and geographic shift.

## 2. VARUNA problem definition

Target workflow: Sentinel-1 SAR → oil-slick segmentation → look-alike filtering → AIS candidates → dark-vessel candidates → environmental reverse drift → multimodal scoring → calibrated ranked sources/abstention. The uploaded project guide specifies the main datasets and module assignments.

## 3. Existing capability landscape

| Area | Existing capability | VARUNA gap |
|---|---|---|
| SAR oil-slick detection | Sentinel-1 ML/segmentation is established; Cerulean uses a ResNet34 U-Net on Sentinel-1 VV. | Not novel by itself. |
| Look-alike rejection | Five-class datasets and ESSD 2025 explicitly include look-alikes. | Generalization and low false alarms remain difficult. |
| SAR + AIS association | Cerulean uses parity, proximity and temporality with AIS tracks. | Use as baseline, not novelty. |
| Dark vessels | xView3-SAR is an open vessel benchmark; Cerulean now uses dark-object detections. | Detection exists; integrated attribution is the gap. |
| Near-real-time | Cerulean surfaces recent detections within hours; AIS can lag. | Near-real-time detection ≠ attribution. |
| Drift/backtracking | Lagrangian/OpenDrift with currents/wind is established. | Integrate physics and uncertainty into source ranking. |
| Definitive culpability | Existing systems explicitly treat links as potential associations. | Still an open problem. |

## 4. Dataset landscape

| Dataset | Documented scale | Use / limitation |
|---|---|---|
| VARUNA Zenodo Parts I–III | Guide: main set ~1,200 images; Part I ~40.9 GB; 2048² VV+VH TIFF + masks. | Segmentation; no vessel culpability labels. |
| Krestenitis/MKLab | ~1,112 S1 images; 1,002 train / 110 test; 5 classes. | Oil/look-alike/ship/land/sea; limited geography. |
| ESSD 2025 Eastern Mediterranean | 3,225 oil objects in 1,365 patches + 2,290 look-alike/other patches; 2019. | Strong look-alike benchmark; one region/year. |
| MarineCadastre AIS | Real US ship tracks; MMSI, position, SOG, COG, vessel type. | Traffic validation; not Indian EEZ. |
| xView3-SAR | Open Sentinel-1 vessel benchmark + reference model. | Vessel detection ≠ pollution attribution. |
| CMEMS + ERA5 | Current forecast/reanalysis + hourly wind. | Environmental model error must enter uncertainty. |

## 5. Feature-level gap

| Feature family | Existing use | Opportunity |
|---|---|---|
| SAR VV/VH, backscatter, texture, shape | VV common; multi-polarization and geometry increasingly used. | Use VV+VH + geometry/context and prove gain. |
| Slick geometry | Area, length, perimeter, elongation and centerline support association. | Evidence, not final attribution. |
| AIS position/time/SOG/COG/track | Core to vessel association. | Track-history consistency and gap-aware candidates. |
| Wind/current | Established for transport. | Ensemble hindcast + uncertainty. |
| Dark-vessel evidence | xView3-SAR and Cerulean demonstrate detection/source use. | Fuse dark and AIS candidates. |
| Temporal evidence | AIS windows and slick-age logic used. | Benchmark degradation as age/latency grows. |

## 6. Benchmark landscape

Detection/segmentation: Krestenitis 2019 and later Sentinel-1 datasets. Look-alike: ESSD 2025. Vessel detection: xView3-SAR. Attribution: Cerulean geometric matching. Drift: Lagrangian/OpenDrift with CMEMS/ERA5.

**Key gap:** a public reproducible source-attribution benchmark with known origin, decoys, AIS gaps and environmental forcing.

## 7. Top 10 genuine gaps

| # | Gap | Class | VARUNA opportunity |
|---|---|---|---|
| 1 | Uncertainty-aware source attribution | Open/integration | Combine slick geometry, AIS history, dark-vessel evidence and drift into calibrated source probabilities. |
| 2 | Slick-age robustness | Validation/operational | Benchmark attribution as slick age and AIS delay increase. |
| 3 | AIS gaps/false broadcasts | Operational/open | Use SAR vessel evidence and track consistency instead of trusting AIS blindly. |
| 4 | Indian-EEZ attribution benchmark | Dataset/benchmark | Public resources are detection-centric; no widely adopted source-attribution benchmark. |
| 5 | Cross-region look-alike generalization | Validation | Use geographic holdouts, not only random splits. |
| 6 | Physics-informed uncertainty | Open research | Ensemble wind/current forcing and propagate drift uncertainty. |
| 7 | Dark-vessel fusion | Integration | Rank AIS and non-AIS candidates in one calibrated framework. |
| 8 | Ablation evidence | Research | Prove incremental value of AIS, drift, dark-vessel and look-alike modules. |
| 9 | Calibration/abstention | Research | Allow "insufficient evidence" instead of forced culprit labels. |
| 10 | Operational latency | Operational | Measure data availability, inference and attribution latency separately. |

## 8. Claims VARUNA should NOT make

- Not the first Sentinel-1 oil-spill detector.
- Not the first SAR + AIS pollution-monitoring system.
- Not the first dark-vessel detector.
- Not a system that proves legal responsibility from satellite/AIS alone.
- Not "real-time vessel attribution" unless end-to-end data latency is demonstrated.

## 9. Strongest defensible novelty

**Conservative:** multimodal uncertainty-aware source attribution.

**Strong:** significant improvement over Cerulean-style geometry under slick-age growth, AIS gaps and environmental uncertainty.

**Ambitious:** a reproducible Indian-EEZ attribution benchmark plus calibrated physics-informed ranking that generalizes.

## 10. Research contribution statement

Position VARUNA as an evidence-fusion and attribution study, not another image-classification study. Test whether physical drift constraints and multimodal vessel evidence produce better-calibrated ranked candidate sources under incomplete observations.

## 11. Experiments that can prove the gap

| ID | Question | Data | Baseline | Metrics | Stress test |
|---|---|---|---|---|---|
| E1 | Detection | Krestenitis/Zenodo + ESSD | U-Net/modern baseline vs NETRA | F1, IoU/Dice, FP rate | Cross-region holdout |
| E2 | Attribution | Synthetic Indian AIS + OpenDrift + real AIS | Cerulean geometry vs VARUNA | Top-1/3, MRR, location error | Slick age/AIS gaps |
| E3 | Dark vessel | xView3-style SAR + decoys | AIS-only vs AIS+SAR vessel | Top-k attribution | Hide guilty vessel from AIS |
| E4 | Ablation | Same simulation harness | SAR → +AIS → +drift → +dark | Δ metrics | Show each modality value |
| E5 | Calibration | All outputs | Probability + abstention | Brier/ECE | Stress uncertain cases |

## 12. Recommended baselines & metrics

**Baselines:** Krestenitis-style segmentation + modern U-Net/transformer; Cerulean parity/proximity/temporality; xView3-SAR; OpenDrift.

**Metrics:** F1/IoU/Dice; look-alike false-positive rate; Top-1/3, MRR, source-location error, Brier/ECE; drift position/temporal error; latency and false alarms.

## 13. Final research position

The strongest defensible contribution is a reproducible, uncertainty-aware multimodal attribution framework testing whether slick evidence, AIS history, dark-vessel evidence and environmental backtracking improve candidate-source ranking under missing data and slick-age uncertainty. The system should abstain when evidence is insufficient.

## 14. References

- SkyTruth Cerulean Methods — https://skytruth.org/cerulean/methods
- SkyTruth FAQ — https://skytruth.org/faq
- SkyTruth, Dark Vessels as Sources (2025) — https://skytruth.org/product-updates/dark-vessels-as-sources
- SkyTruth, Near Real-Time Coming to Cerulean (2026) — https://skytruth.org/blog/near-real-time-coming-to-cerulean
- Krestenitis et al. (2019) — https://doi.org/10.3390/rs11151762
- Yang et al. (2025), ESSD dataset — https://doi.org/10.5194/essd-17-6807-2025
- CSIRO Sentinel-1 dataset (2022) — https://doi.org/10.25919/4v55-dn16
- xView3-SAR — https://arxiv.org/abs/2206.00897
- VARUNA Master Dataset Guide (uploaded project document), pp. 1–9.
