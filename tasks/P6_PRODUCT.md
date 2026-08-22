# P6 — PRODUCT / DEMO / RESEARCH
## Owns: Narrative · demo cases · slides · Q&A · rehearsal · backup video

You decide what the room sees and remembers. You are also the only line of defense
against the honesty rules getting broken under pressure. Read `CLAUDE.md` and
`docs/DECISIONS.md` before anything — especially §1, because the headline claim you'd
naturally reach for ("100% accuracy") is not one we can make yet.

---

## Day-by-Day

### Day 1 — the two blockers
- **Email your college library for the MPB 2024 paper**: "A new ship tracing technology
  from oil spills based on multi-source data," Luo et al., DOI
  `10.1016/j.marpolbul.2024.116808`, PMID 39146713. This is the closest prior art and it
  has not been read — do not let novelty claims outrun this. Also try inter-library loan
  and a polite email to the corresponding author for a preprint.
- **Apply for the Krestenitis/MKLab dataset**: needs an institutional email, a project
  title + abstract, and supervisor sponsorship. `m4d.iti.gr/oil-spill-detection-dataset/`.
  Start this today — it has a human in the loop and will not move at software speed.
- Pick the three demo regions with P3 (Arabian Sea/Mumbai High, Bay of Bengal/Chennai,
  Gulf of Mexico) so forcing/scene caching can start immediately.

### Day 2 — storyboard
- Draft the six demo moments (master context §15.1) as a shot list with exact screen
  states, not just prose. Moment 3 (judge controls) gets the most detail — it is choreo-
  graphed, not improvised.
- Start the PPT skeleton (10 slides max, SIH format). Slide order should mirror the
  10-minute script in §15.2.

### Day 3 — read the paper, update the claim
- Read the MPB 2024 paper in full once it arrives. Confirm or revise: does Luo et al. use
  ensemble uncertainty, a probability field, a latent-source hypothesis, or calibration?
  Current working read is *no* to all four — a deterministic bidirectional comparator. If
  that holds, our differentiation survives intact; cite it properly either way.
- Write the citation and the one-line differentiation into the PPT: "Luo et al. (2024)
  demonstrated bidirectional Lagrangian drift for trajectory similarity. We extend this by
  treating the source as a probability field under ensemble uncertainty, competing named
  vessels against an explicit unobserved-source hypothesis."

### Day 4 — evidence slide + hotspot dataset
- Once P1's rebuilt sweep lands, build the accuracy-vs-age evidence slide from the real
  CSV — not from the invalid 100% run. If the number is lower than hoped, that is the
  honest slide; Section 15.1 Moment 6 exists precisely to make an honest "we don't know"
  read as maturity rather than weakness.
- Build or simulate a season of case history for SMRITI's hotspot corridor (Demo Moment
  5) if P4's real case volume is thin.

### Day 5 — Q&A document
- Write out the ten killer questions from the roadmap (§3.3) plus the four hardest ones
  from this session's review (simulated-only evaluation, calibration on simulated truth,
  "how is this different from Cerulean," synthetic Indian AIS) — full prepared answers,
  memorized, not read off a card.
- Cross-check every claim in the deck against `CLAUDE.md`'s honesty rules line by line.
  Anything that says "unsolved," "patentable," "real-time," or "no Indian system exists"
  gets rewritten before it reaches a slide.

### Day 6 — rehearse
- Full run-through against P1/P4/P5's actual working pipeline, not slides alone. Time it
  against the §15.2 script blocks.
- Record the **3-minute backup video** the first time the pipeline works end to end, not
  the night before submission. A working system today beats a polished one that only
  exists tomorrow.

### Day 7 — submit
- Finalize and submit the idea PPT. State the synthetic-AIS position explicitly, in your
  own words, before a judge can ask.
- Rehearse again. Confirm P4/P6 have the SSD packed with cached cases, forcing data, and
  model weights, tested on a second machine.

---

## Files You Create

| Path | Purpose |
|---|---|
| `docs/demo_storyboard.md` | Six moments, shot-by-shot |
| `docs/qa_prep.md` | Killer questions + memorized answers |
| `docs/submission.pptx` (or `.md` source) | The idea deck |
| `docs/mpb2024_notes.md` | Reading notes + the differentiation paragraph |
| `data/demo_cases/*.json` | Frozen case definitions per demo region |

## The honesty checklist (run this against every slide, every time)

- [ ] Never "attribution is unsolved" — Cerulean and CleanSeaNet ship it.
- [ ] Never "backward drift is our innovation" — the PS asks for it; Seatrack has done it
      20 years. Ours is the *probabilistic formulation*.
- [ ] Never present simulated evaluation as operational validation.
- [ ] Never hide that Indian AIS is synthetic — say it before asked.
- [ ] Never "patentable" — only "potentially patent-relevant."
- [ ] Never "real-time" — Sentinel-1 revisit is days; that's *why* backward inference.
- [ ] Never "no Indian system exists" as fact — "no publicly documented system."
- [ ] The system never names a ship without human sign-off.

## Interfaces

- **CONSUME:** everything, eventually — you are the integration point for the *story*,
  not the code.
- **PRODUCE:** the frozen demo case list (→ P2, P3 for caching), the PPT, the video.
- **NEED FROM:** P1 by day 4 — the real (not invalid) accuracy-vs-age curve. Everyone by
  day 6 — a working pipeline to rehearse against.

## Claude Code Prompt

```
Read CLAUDE.md, docs/DECISIONS.md, and tasks/P6_PRODUCT.md. You are P6, product/demo.
You own the narrative, the six demo moments, the submission deck, Q&A prep, and
honesty-rule compliance across everything the team produces.

Critical context: the project's original go/no-go result (100% top-1 accuracy) is
invalid — see docs/DECISIONS.md section 1. Do not write that number into any slide or
document. Wait for P1's rebuilt sweep and use that number, whatever it is.

Start now: draft docs/demo_storyboard.md, expanding the six moments in
VARUNA_MASTER_CONTEXT.md section 15.1 into an exact shot list — screen state before,
action, screen state after, spoken line — for each moment. Moment 3 (judge controls)
gets the most detail.
```

## If Claude Is Offline

- MPB 2024 paper DOI: `10.1016/j.marpolbul.2024.116808`. Try your library's inter-library
  loan portal first; Sci-Hub is a fallback, not a first move, given institutional policy.
- Cerulean methods reference for the Q&A: https://skytruth.org/cerulean/methods
- SIH submission format: 10 slides max, per the master context §1. Check the current
  year's exact template on the SIH portal before finalizing layout.
- Keep every honesty-rule check as a literal checklist pass over the final deck, slide by
  slide, out loud, with a second person — it is much easier to skip when reading silently.
