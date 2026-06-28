# Round-number anchoring in vision-LLM number estimation

A follow-up to the [number-sense](../README.md) study. Tests whether vision-LLMs, when
estimating "how many objects?", **anchor their answers on round numbers** (multiples of 5/10)
the way humans do — and finds that it depends heavily on the model.

## Why this study exists

The main number-sense study used set sizes 15, 20, 25, 30, 40 at the high end. Those are
*themselves* almost all round numbers, so they cannot test for round-number anchoring: the
models were essentially never shown a non-round quantity in the range where rounding would
surface. A claim either way ("models anchor" / "models don't") would have been unsupported by
that design.

So we ran a dedicated test: **every integer from 25 to 40** (round anchors 25/30/35/40
interleaved with non-round fillers 26–29, 31–34, 36–39), 15 distinct layouts × 15 calls = 225
fresh calls per true count, per model. Dot size is jittered so total area is decorrelated from
count (area plateaus across 25–40), so any clustering reflects *number*, not ink. Same neutral
wording ("How many objects are in this image?"), collect-only, scored by reading the responses.

## How to read the result

The decisive view is **modal response vs. true count** (the single most common answer at each
true N):

- **Anchoring** looks like a *staircase*: the modal answer stays flat across a run of true
  counts (e.g. locked on 25 for true 25, 26, 27, …) and only jumps when forced to the next round
  value. The model's most likely answer ignores the true count.
- **Honest estimation** looks like a *diagonal*: the modal answer climbs with the true count.

(We avoid leaning on "% of answers that are a multiple of 5" as the headline: at true N = 25,
answering "25" is also just *correct*, so that metric conflates anchoring with accuracy. The
modal staircase and the per-N histograms are the clean signals.)

## Result: all three models anchor — differing in strength

![three-model comparison](figures/anchor_three_model.png)

Every model's modal answer locks onto values and holds them across runs of consecutive true counts
before stepping — a **staircase**, not a smooth diagonal. Modal sequences (true 25 → 40):

- **Grok:**  `25 25 25 25 25 25 25 25 25 25 25 32 32 40 40 40`
- **Gemini:** `25 26 26 26 26 30 30 30 30 31 30 33 35 35 36 36`
- **Llama:**  `20 25 28 23 27 30 31 30 30 33 36 39 40 40 40 40`

Gemini's mode holds ~26 across true 26–29, then locks on **30** across 30–33, climbs in steps, and
reaches only 35–36 even at true 40. Llama (noisier) bounces near 25 for 25–29, sticks near **30**
for 30–33, then climbs and locks on **40** for the top four. Grok shows the same behavior in extreme
form (its mode holds the value 25 across true counts 25–35).

Quantitatively (true 25–40; a non-anchoring estimator gives a modal multiple-of-5 at ~4/16 and ~20%
of all answers on a multiple of 5):

| Measure | Grok (xAI) | Gemini (Google) | Llama (Meta) |
|---|---|---|---|
| True counts whose **mode is a multiple of 5** | **14 / 16** | 8 / 16 | 9 / 16 |
| Widest **capture zone** (consecutive counts on one locked mode) | **11** (value 25) | 4 (26, 30) | 4 (40) |
| Share of **all** answers on a multiple of 5 | **55 %** | 25 % | 26 % |

- **All three under-estimate** (mean below the true count, gap widening with N) — a shared compression.
- **All three anchor** — their modal answers form round-number plateaus. They differ in **strength**:
  Grok is extreme (an 11-count capture zone on 25; 55% of all answers round), while Gemini and Llama
  are milder (≈4-count plateaus; bulk distributions only just above the ~20% chance rate, but the
  *mode* still locks into round treads). Per-model views:
  [grok](figures/anchor_grok_hist_curve.png), [gemini](figures/anchor_gemini_hist_curve.png),
  [llama](figures/anchor_llama_hist_curve.png).

**Takeaway:** round-number anchoring — a documented human estimation strategy (anchoring-and-
adjustment; people cluster numerosity estimates on round values, e.g. Tversky & Kahneman 1974;
Solstad et al. 2026) — appears in **all three** models from three independent labs. It is
**architecture-general in kind but model-specific in degree**: every model anchors, and they differ
markedly in how wide the capture zones are and how strongly responses pile onto round values.

## Honest caveats

- **Llama is the noisiest model** (smallest of the three). ~5–8% of its responses per cell were
  refusals, garbled output, or wild outliers (e.g. 113, 1372, 35000); those were dropped during
  reading. Its "tracking" is real but messy. Its noise partly reflects capacity, not just a
  different number sense.
- **Scoring is by reading.** The `ai_read_answers.json` per model contains the values a reader
  extracted from the raw responses (with X for refusals/garble). The `raw.jsonl` holds every
  verbatim response — re-score it if you want to check us. See [`../../PROTOCOL.md`](../../PROTOCOL.md).
- **Three small/cheap models, one prompt, one session.** Whether anchoring emerges at frontier
  scale, or under different prompts, is open.

## Files

```
anchoring/
├── stimuli/manifest.csv          # the dense 25-40 stimulus set (ground truth; PNGs regen from gen_stimuli.py seed 113)
├── data/<model>/raw.jsonl        # every verbatim response (225 per true count)
├── data/<model>/ai_read_answers.json   # answers scored by reading
├── figures/anchor_<model>_hist.png      # per-true-N response histograms
├── figures/anchor_<model>_hist_curve.png # mean & modal vs true count
├── figures/anchor_three_model.png        # the decisive 3-model comparison
├── plot_anchor.py                # render per-model figures from ai_read_answers.json
└── plot_three.py                 # render the 3-model comparison
```

Regenerate the stimuli: `python3 ../gen_stimuli.py --sizes 25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40 --reps 15 --types A --seed 113 --out stimuli`
