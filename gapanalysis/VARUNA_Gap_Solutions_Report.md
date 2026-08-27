# VARUNA — Gap Resolution Plan
### How to close each of the 10 identified research gaps
SIH 2026 / SIH26143

---

## 1. Uncertainty-aware source attribution
**Class:** Open / integration

**Solution approach**
- Build a late-fusion scoring model that takes four evidence streams as input: slick geometry features (NETRA), AIS track features (NYAYA), dark-vessel SAR detections (CHHAYA), and drift-backtrack likelihood surfaces (PRATIVARTAN/PRAVAAH).
- Use a probabilistic ranking model (e.g. gradient-boosted ranker or Bayesian fusion) that outputs a calibrated probability distribution over candidate vessels rather than a single hard label.
- Train/validate on the E2 experiment harness (synthetic Indian AIS + OpenDrift + real AIS) against the Cerulean geometry baseline, measuring Top-1/3, MRR, and location error.

**Owner modules:** NETRA + NYAYA + CHHAYA + PRATIVARTAN/PRAVAAH (fusion layer sits above all four)

---

## 2. Slick-age robustness
**Class:** Validation / operational

**Solution approach**
- Generate synthetic test cases where slick age is systematically varied (0–72 hrs) and AIS reporting delay is varied independently.
- Measure attribution accuracy decay curves — accuracy vs. age, accuracy vs. AIS delay — instead of a single-point metric.
- Add slick-age as an explicit input feature to the fusion model (not just a filtering threshold) so the model learns to down-weight stale geometric evidence and up-weight drift-based evidence as age increases.

**Owner modules:** PRATIVARTAN/PRAVAAH (drift), fusion layer

---

## 3. AIS gaps / false broadcasts
**Class:** Operational / open

**Solution approach**
- Cross-check every AIS-reported position against SAR-detected vessel positions (from CHHAYA/xView3-style detector) for consistency; flag mismatches as "AIS unreliable" rather than trusting AIS blindly.
- Model AIS as a noisy sensor with a learned reliability score per vessel/time-window, derived from track-continuity, speed-jump anomalies, and gap duration.
- When AIS is missing or flagged unreliable, fall back to dark-vessel detection + drift-based candidate generation.

**Owner modules:** NYAYA (AIS reliability scoring) + CHHAYA (cross-check)

---

## 4. Indian-EEZ attribution benchmark
**Class:** Dataset / benchmark

**Solution approach**
- Construct a synthetic but physically grounded benchmark: simulate spills at known origin points within the Indian EEZ, run OpenDrift with CMEMS + ERA5 forcing to generate realistic slick shapes, and inject synthetic AIS tracks (including decoys and dropout) for candidate vessels.
- Publish the benchmark generation pipeline (not just a static dataset) so it is reproducible and extensible to new regions.
- Include ground-truth origin, decoy vessels, AIS-gap scenarios, and known environmental forcing as required benchmark fields — this is the "public reproducible source-attribution benchmark" identified as missing in the gap analysis.

**Owner modules:** New dataset-generation submodule feeding NETRA/NYAYA/CHHAYA/PRATIVARTAN

---

## 5. Cross-region look-alike generalization
**Class:** Validation

**Solution approach**
- Replace random train/test splits with strict geographic holdouts (train on Mediterranean ESSD 2025 + Krestenitis regions, test on Indian-EEZ-simulated regions).
- Report false-positive rate and F1 separately per region to expose generalization gaps rather than averaging them away.
- Apply domain-adaptation techniques (e.g. style-transfer augmentation on SAR texture, or fine-tuning on a small labeled Indian-EEZ subset) if cross-region performance drops significantly.

**Owner modules:** NETRA (look-alike rejection head)

---

## 6. Physics-informed uncertainty
**Class:** Open research

**Solution approach**
- Run OpenDrift as an ensemble (varying wind/current forcing within CMEMS/ERA5 error bounds) instead of a single deterministic trajectory, producing a probability surface rather than one backtrack line.
- Propagate this drift uncertainty forward into the fusion model as a spatial likelihood map, so candidate vessels are scored against a probability field, not a point estimate.
- Validate ensemble spread against known-origin synthetic cases (E2) to confirm the uncertainty is well-calibrated (not just wide).

**Owner modules:** PRATIVARTAN/PRAVAAH

---

## 7. Dark-vessel fusion
**Class:** Integration

**Solution approach**
- Run the xView3-SAR-style dark-vessel detector alongside AIS-based candidate generation, producing two candidate lists per event.
- Merge both lists into one calibrated ranking framework (same scoring model as Gap 1) rather than treating dark-vessel detection as a separate fallback pipeline.
- Stress-test with E3: deliberately hide the guilty vessel from AIS and confirm the dark-vessel channel still surfaces it in the Top-k ranking.

**Owner modules:** CHHAYA + fusion layer

---

## 8. Ablation evidence
**Class:** Research

**Solution approach**
- Use the E4 experiment: run the same simulation harness through four configurations — SAR only → +AIS → +drift → +dark-vessel — and report the metric delta (ΔF1, ΔTop-1/3, ΔMRR) at each step.
- Publish this as a core results table in the final report/paper; it is the direct evidence that integration (not any single component) is the contribution.

**Owner modules:** All four, orchestrated by fusion layer

---

## 9. Calibration / abstention
**Class:** Research

**Solution approach**
- Add an explicit "insufficient evidence" output class to the fusion model, triggered when top-candidate probability falls below a calibrated confidence threshold.
- Use E5: evaluate calibration quality with Brier score and Expected Calibration Error (ECE), not just accuracy.
- Deliberately construct low-evidence stress cases (old slick, no AIS, no dark-vessel detection, high drift uncertainty) and confirm the system abstains rather than forcing a guess.

**Owner modules:** Fusion layer (final decision stage)

---

## 10. Operational latency
**Class:** Operational

**Solution approach**
- Instrument and separately log three latency components: (a) data availability latency — time from satellite pass to data access; (b) inference latency — time for detection + segmentation models to run; (c) attribution latency — time for the fusion/ranking stage to produce a ranked output.
- Report all three separately rather than a single "system latency" number, since Cerulean-style near-real-time detection does not imply near-real-time attribution.
- Set target latency budgets per stage and benchmark against them under realistic data-availability delays (AIS lag, satellite revisit time).

**Owner modules:** Full pipeline instrumentation

---

## Suggested execution order

1. **Foundation (Weeks 1–3):** E1 detection baseline (NETRA) + Indian-EEZ synthetic benchmark generation (Gap 4)
2. **Core integration (Weeks 4–7):** AIS reliability scoring (Gap 3) + dark-vessel fusion (Gap 7) + fusion-model v1 (Gap 1)
3. **Robustness (Weeks 8–10):** Slick-age stress tests (Gap 2) + physics-informed drift ensembles (Gap 6) + cross-region validation (Gap 5)
4. **Evidence & polish (Weeks 11–13):** Ablation study (Gap 8) + calibration/abstention (Gap 9) + latency instrumentation (Gap 10)

This sequencing front-loads the benchmark and detection baseline (needed by everything downstream), builds the fusion core next, then spends the back half proving robustness and producing the ablation/calibration evidence that makes the novelty claim defensible.
