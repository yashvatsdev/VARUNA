# FAILURE_THREAT_MATRIX.md
## VARUNA GRID v2 — threats, containment, degraded behaviour, tests

Every row must have exactly one **architectural containment location**. If a new failure
has no containment location, that is an architecture gap requiring an ADR — not a
defensive `try/except` at the call site.

**Severity:** P0 = can produce a confidently wrong accusation, an unsafe dispatch, or
evidence loss. P1 = degrades correctness or availability visibly. P2 = quality/UX.

**Test column** names the file that must exist. `tests/robustness/` is the default home.
A P0 row without a passing test is a release blocker.

---

## 1. External source failures

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| S-01 | CMEMS/ERA5 timeout or outage | P1 | Source Adapter | Request timeout, retry exhaustion | Cache → snapshot → climatology | `degradation_state=FALLBACK_SOURCE`, trust→DEGRADED, w=0.6 | Auto-retry with backoff; resume live on recovery | Banner: "forcing from climatology — origin field unreliable" | `test_adapter_fallback_chain.py` |
| S-02 | Rate limit / auth failure | P1 | Source Adapter | HTTP 429/401 | Token-bucket limiter, credential health check | Serve cache; queue job | Refresh credentials; backoff | "Data source unavailable, using cached" | `test_adapter_rate_limit.py` |
| S-03 | Partial/truncated response | P0 | Data Guard | Completeness + coverage check | Reject; do not pad | `INCOMPLETE_COVERAGE`, trust→DEGRADED | Re-fetch | Coverage gap shown on map | `test_data_guard_completeness.py` |
| S-04 | Silent schema/product version change | P0 | Data Guard | Schema validation + version capture | Quarantine batch | `SCHEMA_MISMATCH`, trust→QUARANTINED, w=0 | Human review; adapter update | "Source format changed — quarantined" | `test_data_guard_schema_drift.py` |
| S-05 | Unit or CRS mismatch | P0 | Data Guard | Unit/CRS assertions vs declared | Reject before inference | `UNIT_MISMATCH` / `CRS_MISMATCH`, QUARANTINED | Adapter fix | Explicit error, case blocked | `test_data_guard_units_crs.py` |
| S-06 | Stale data served as current | P0 | Data Guard | Freshness vs observation time | Trust downgrade proportional to staleness | `STALE`, trust→DEGRADED | Re-fetch | Age of forcing displayed | `test_data_guard_staleness.py` |
| S-07 | **Correlated source bias** (CMEMS + ERA5 share a parent model) | P0 | Data Guard | Cross-source consistency + dependency registry | Reduce *combined* influence, not each independently | `CORRELATED_SOURCE_BIAS`; ensemble spread widened | Use structurally different products | "Forcing sources are not independent" | `test_data_guard_correlated_bias.py` |
| S-08 | Compromised/manipulated source | P0 | Data Guard | Statistical + physical plausibility, source drift | Quarantine; retain raw | `SUSPECTED_MANIPULATION`, w=0 | Human review; PRAMAN preserves raw | "Source quarantined pending review" | `test_data_guard_manipulation.py` |

---

## 2. AIS-specific threats

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| A-01 | AIS spoofing (false position) | P0 | Data Guard + Flow Inspection | Implied speed, impossible transitions, kinematic consistency | Down-weight track influence | `IMPLIED_SPEED_IMPOSSIBLE`; `ais_reliability` ↓ | Flag vessel; latent hypothesis absorbs residual | Vessel marked "position implausible" | `test_ais_spoofing.py` |
| A-02 | AIS gaps 20–120 min | P1 | AIS track builder | Gap detection | Interpolate **and inflate `position_std_km`** | Uncertainty widens; `ais_reliability` ↓ | None needed | Gap segments dashed on map | `test_ais_gaps.py` |
| A-03 | Transponder off (true dark vessel) | — | NYAYA + CHHAYA | Absence from AIS + radar contact | Latent-source hypothesis L₀ | `LATENT_SOURCE` decision state | Sensor tasking cue | "Latent source dominant" | `test_latent_source_detection.py` |
| A-04 | MMSI collision / identity reuse | P1 | Data Guard | Duplicate MMSI, discontinuous kinematics | Split into separate tracks | Both scored; neither named confidently | Human review | "Ambiguous vessel identity" | `test_ais_mmsi_collision.py` |
| A-05 | Sparse coverage → false "dark" | P0 | CHHAYA | Scene footprint vs AIS coverage | `INSUFFICIENT_COVERAGE`, never a dark claim | No latent conclusion drawn | Widen AIS window | "Coverage insufficient to conclude" | `test_chhaya_coverage_gap.py` |

---

## 3. Physics and Φ

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| P-01 | **Convergence collapse** (ensemble does not agree) | P0 | Φ diagnostics → Validity Gate | Ensemble-split divergence metric | `convergence_flag=NOT_CONVERGED` | Validity → RESTRICTED; no vessel named | Increase M; better forcing | "Origin field did not converge" | `test_phi_convergence_failure.py` |
| P-02 | **Multimodal Φ** (two competing origins) | P0 | Φ diagnostics → NYAYA | Mode detection, separation distance | Report `n_modes`, `multimodal=True` | `NOT_DISTINGUISHABLE` if candidates split across modes | Human review both lobes | Both lobes drawn; "two possible origins" | `test_phi_multimodal.py` |
| P-03 | Current-field bias (structural, not jitter) | P0 | Ensemble construction | Sensitivity analysis | Structurally varied members (different products) | `forcing_sensitivity` high → uncertainty widened | Multi-product ensemble | "Result sensitive to forcing choice" | `test_forcing_bias_sensitivity.py` |
| P-04 | Age prior dominates the answer | P0 | Sensitivity block | `age_sensitivity` computed | Surface `dominant_assumption` | Validity → DEGRADED with caveat | Better age model | "Origin driven by age assumption" | `test_age_sensitivity.py` |
| P-05 | Weathering irreversibility misuse | P0 | PRATIVARTAN | Static check: `OpenOil` forbidden in backward path | Use `OceanDrift` for backtracking | n/a — prevented | Code review + test | n/a | `test_backtrack_uses_oceandrift.py` |
| P-06 | Compute blowout / runtime exceeded | P1 | PRATIVARTAN | Wall-clock budget | Reduce M; **never silently truncate** | `REDUCED_ENSEMBLE`, uncertainty widened | Scale hardware | "Reduced ensemble — wider uncertainty" | `test_ensemble_reduction.py` |
| P-07 | Particle loss (beaching, domain exit) | P1 | Φ diagnostics | `particles_lost` vs seeded | Report ratio; flag boundary interaction | Trust→DEGRADED if >20% lost | Expand domain | "Particles left the domain" | `test_particle_loss.py` |
| P-08 | Φ not normalised | P0 | Flow Inspection | `abs(sum − 1) > 1e-6` | Reject artifact | `PROBABILITY_NOT_NORMALISED`; case blocked | Fix producer | Hard error | `test_phi_normalisation.py` |

---

## 4. Attribution and calibration

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| N-01 | **Flat posterior treated as an answer** | P0 | NYAYA → Validity Gate | Normalised entropy > threshold | `INCONCLUSIVE` | No vessel named; search box still emitted | More/better evidence | "Inconclusive — narrowed search box provided" | `test_flat_posterior_inconclusive.py` |
| N-02 | **Two vessels in the same Φ lobe** | P0 | NYAYA | `distinguishability` low despite sharp posterior | `NOT_DISTINGUISHABLE` | Both listed; neither named | Human review | "Cannot separate top candidates" | `test_not_distinguishable.py` |
| N-03 | Miscalibrated posterior | P0 | Calibration + Validity Gate | ECE on held-out sweep; OOD check | `calibration_state=OUT_OF_DOMAIN` | Probabilities shown as scores, not probabilities | Refit isotonic | "Uncalibrated — treat as ranking only" | `test_calibration_ood.py` |
| N-04 | Latent term degenerate (constant) | P0 | NYAYA | Contract test: L₀ must vary with track geometry | Residual corridor computation | n/a — prevented | Code fix | n/a | `test_latent_not_constant.py` |
| N-05 | Prior overwhelms evidence | P1 | NYAYA | Prior vs evidence contribution reported separately | Cap prior influence | Both contributions shown in UI | Retune weights | Score breakdown visible | `test_prior_evidence_balance.py` |
| N-06 | Calibration trained on invalid harness | P0 | Evaluation | Harness validity checklist (see §8) | Block calibration fit on invalid sweep | Uncalibrated until harness rebuilt | Rebuild harness | "Calibration pending" | `test_harness_validity_gate.py` |

---

## 5. Operational decision and response

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| O-01 | **Asset dispatched on weak evidence** | P0 | Validity Gate + case invariants | `outcome.supports_dispatch` check | Invariant rejects state | Dispatch blocked | Human override with recorded reason | "Cannot dispatch on this outcome" | `test_evidence_envelope.py` ✅ |
| O-02 | **Action without human authorization** | P0 | Mission FSM | `human_approved_by` required for ASSIGNED | `transition()` raises | Action blocked | Officer approves | Approval dialog | `test_evidence_envelope.py` ✅ |
| O-03 | Infeasible assignment (out of range/endurance) | P1 | ABHIYAN feasibility filter | Range, endurance, sea state | Filter before optimisation | Asset excluded with reason | Different asset | "Asset out of range" | `test_abhiyan_feasibility.py` |
| O-04 | Asset double-booked | P1 | Mission FSM | Reservation before assignment | `RESERVED` state | Second request rejected | Reassign | "Asset already committed" | `test_mission_double_booking.py` |
| O-05 | AI recommendation recorded as human decision | P0 | PRAMAN + missions | Separate fields, never merged | Schema separation | n/a — prevented | n/a | Both shown distinctly | `test_evidence_envelope.py` ✅ |
| O-06 | Case closed with asset airborne | P0 | Case invariants | `check_case_invariants` | Rejected | Close blocked | Recover asset first | "Asset still committed" | `test_evidence_envelope.py` ✅ |

---

## 6. Alerts and external action

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| L-01 | Alert on unverified detection | P0 | Alerts materiality filter | Validity state check | Block below threshold | No external send | Verify first | "Alert withheld — unverified" | `test_alert_materiality.py` |
| L-02 | Alert to wrong audience | P1 | Role router | RBAC + role mapping | Route by role | Held for review | Fix routing | Delivery log | `test_alert_routing.py` |
| L-03 | Stale alert delivered late | P1 | Freshness check | Age vs validity window | Suppress expired | Not sent | Regenerate | "Alert expired" | `test_alert_freshness.py` |
| L-04 | Simulated provider presented as live | P0 | Alerts + docs | Provider status label required | Label enforced in schema | n/a — prevented | n/a | "SIMULATED" badge | `test_alert_provider_labelling.py` |
| L-05 | Alert storm / duplicate sends | P1 | Alerts dedupe | Idempotency key per case+channel | Dedupe window | Single send | n/a | Delivery log shows dedupe | `test_alert_dedupe.py` |

---

## 7. Platform, security, governance

| ID | Threat | Sev | Contained at | Detection | Containment | Degraded behaviour | Recovery | User sees | Test |
|---|---|---|---|---|---|---|---|---|---|
| G-01 | Event ordering violation | P1 | Event Spine | Monotonic sequence per case | Reject out-of-order | Event parked | Replay in order | Case timeline consistent | `test_event_ordering.py` |
| G-02 | Raw evidence overwritten | P0 | PRAMAN | Append-only store + content hash | Write rejected | n/a — prevented | n/a | Immutable history | `test_praman_append_only.py` |
| G-03 | Manifest not reproducible | P0 | PRAMAN | Deterministic serialisation test | Sorted keys, fixed separators | n/a | Fix serialiser | Same hash on re-run | `test_praman_determinism.py` |
| G-04 | Unauthorized access to case data | P0 | RBAC | JWT claims + role check | 403 | Denied | Grant role | Access denied | `test_rbac.py` |
| G-05 | Secret committed to repo | P0 | CI | `bandit`, secret scan, `.gitignore` | Build fails | n/a | Rotate secret | CI red | CI job |
| G-06 | Vulnerable dependency | P1 | CI | `pip-audit`, Trivy | Build fails | n/a | Upgrade | CI red | CI job |
| G-07 | **SMRITI self-reinforcing loop** | P0 | SMRITI pipeline | No online-training code path | Human approval gate before any new version | Model frozen until approved | Offline experiment + validation | "Model version pending approval" | `test_smriti_no_online_training.py` |
| G-08 | Model version drift (unknown weights in prod) | P0 | Model registry | `model_version` stamped on every output | Reject unregistered version | Inference blocked | Register model | Version shown per artifact | `test_model_version_stamped.py` |
| G-09 | LLM alters a scientific number | P0 | LLM boundary | Numbers injected from structured data only | Template-injection only | n/a — prevented | n/a | Report cites source fields | `test_llm_no_number_generation.py` |

---

## 8. Evaluation-harness validity (meta-threat)

| ID | Threat | Sev | Contained at | Detection | Containment | User sees | Test |
|---|---|---|---|---|---|---|---|
| E-01 | **Harness cannot fail** — negatives too easy, baseline handicapped, latent term constant, forcing centred on truth | P0 | `experiments/` review gate | Validity checklist below | Block calibration + block any published number | "Harness invalid — results withheld" | `test_harness_validity_gate.py` |

> **This threat has already materialised once.** The original `experiments/go_nogo/`
> harness reported 100% top-1 at 24 h / 20 vessels. Verified defects: innocent vessels
> drawn a median 33 km from the origin, the guilty track ending 18 h before observation
> so the baseline could never win, `L₀` fixed at `1/(2N+1)`, and the backward ensemble
> centred on the exact truth field. Rebuilt fairly, top-1 fell to ~12%. See
> `docs/DECISIONS.md` §1. Do not publish or calibrate on the old numbers.

**Harness validity checklist** — all must hold before any number leaves `experiments/`:

- [ ] Hard negatives are a swept parameter, with a controlled fraction transiting near the true origin
- [ ] Guilty and innocent vessels broadcast across the same time envelope
- [ ] Baseline is a faithful reimplementation (Cerulean parity/proximity/temporality), not a straw man
- [ ] L₀ varies with track geometry (asserted by `test_latent_not_constant.py`)
- [ ] Forward truth field and backward model field differ **structurally**, not by symmetric jitter
- [ ] Current field has spatial structure (shear, eddies) — not spatially uniform
- [ ] True slick age is **not** passed to the backward run; age is sampled from a prior
- [ ] Trial count gives a CI narrow enough for the claim being made
- [ ] Seeds recorded; run reproducible from the committed config

---

## 9. Demo-day failure

| ID | Threat | Sev | Containment | Recovery |
|---|---|---|---|---|
| D-01 | Live API unavailable | P1 | `DEMO_MODE=true` serves frozen artifacts | Pre-cached, tested on a second machine |
| D-02 | GPU failure | P1 | Cached NETRA outputs + pre-computed Φ | CPU inference path |
| D-03 | Pipeline exception on stage | P1 | Replay mode from recorded session | Recorded video as final fallback |
| D-04 | Network dead | P1 | Air-gapped: local tiles, local weights, local forcing | Nothing external is required |

---

## 10. Coverage rule

```
P0 rows: 27   → each requires a passing robustness/contract test before release
P1 rows: 20   → each requires a test before the finale
P2 rows:  0
```

Currently passing: O-01, O-02, O-05, O-06 (in `tests/contract/test_evidence_envelope.py`).
All others are **PLANNED** — see `SETUP_STATUS.md` for live status.
