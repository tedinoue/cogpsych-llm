# Number sense in vision-language models

A replication of the classic human dot-estimation paradigm, run on vision-LLMs.

## The question

Humans show a remarkably consistent profile when they estimate "how many?" for a set of
objects shown too briefly to count:

1. **Subitizing** — sets of ~1–4 are reported instantly and exactly, with no error.
2. **Weberian estimation** — above ~4, people *estimate*, and the error grows with the
   number being judged (a roughly constant coefficient of variation: scalar variability,
   Weber's law). This analog magnitude system is shared across human cultures — including
   the Pirahã, who lack count words above two yet show the *same* estimation signature as
   numerate adults (Gordon 2004).
3. **Decision strategies on top** — for larger sets people don't just read off a magnitude;
   they *compare to a remembered reference*, *partition and recombine*, and **anchor on
   round numbers** ("I'm gonna say 20"), producing systematic over/under-estimation
   (Tversky & Kahneman 1974; Solstad et al. 2026).

We ran the same task on vision-LLMs and asked: **does the model's number cognition have the
human shape — and where does it diverge?**

This is *not* a benchmark of counting accuracy. It is a measurement of the *shape* of the
model's number sense.

## Design

- **Stimuli** ([`stimuli/`](stimuli/), [`gen_stimuli.py`](gen_stimuli.py)): black circles
  on white, exact known counts, scattered at random non-overlapping positions. Dot sizes are
  jittered so that **total dot-area does not track the count** (it plateaus and even drops at
  high N) — so accuracy can't ride on "more ink = more dots." 16 set sizes
  (1–10, 12, 15, 20, 25, 30, 40), 10 distinct random layouts each. Deterministic from seed.
- **Task**: one neutral prompt, *"How many objects are in this image?"*, asked as fresh
  independent calls. (We deliberately avoid "dots" — see the lexical note below.)
- **n** = 50 per set size (10 layouts × 5 repetitions) per model = 800 calls/model.
- **Models** — three independent labs, each a *non-reasoning* model that **estimates at a
  glance** rather than serially enumerating (enumerators were excluded; see Notes):
  - `grok-4.20-non-reasoning` (xAI)
  - `llama-3.2-11b-vision-instruct` (Meta)
  - `gemini-2.5-flash-lite` (Google)
- **Scoring**: by reading every response (see [`../PROTOCOL.md`](../PROTOCOL.md)). Raw
  responses and the read answer-tables are in [`data/`](data/).

## Results

### The core signature is architecture-general

All three models, from three independent labs, show **subitizing-then-Weberian-estimation**:
near-exact at small set sizes, then estimation whose absolute error grows with the number
judged. The basic shape of the human number sense appears across xAI, Meta, and Google
models. It is not an artifact of any one lab.

### But the fine structure is model-specific — each model has a "numerical personality"

| Feature | Grok (xAI) | Llama-3.2-11b (Meta) | Gemini-2.5-FL (Google) |
|---|---|---|---|
| Subitizing (1–4) | **perfect, zero variance** | imperfect | imperfect (slight over) |
| Estimation precision | medium | **noisiest**, sometimes breaks down | **tightest, most accurate** |
| High-N bias | under-estimates | ~unbiased / slightly over | mild under, tight |
| Round-number anchoring | **strong** (snaps to 25; anchors on 25 for N=30) | none | none |
| Reliability | clean | refusals / garbled outputs | clean (0 failures) |

Three through-lines emerge:

1. **Flawless subitizing is the exception, not the rule.** Only Grok is exact and
   zero-variance at 1–4; the other two err even on tiny sets. The clean human subitizing
   boundary is *not* universal across models.

2. **Estimation precision tracks model quality.** Gemini (the strongest small model here)
   gives the tightest Weber curve and never fails; Llama (the weakest) is the noisiest and
   sometimes breaks down. The analog magnitude system appears universal; its *precision* is
   capability-dependent.

3. **Human-like round-number anchoring is model-specific.** The decision-strategy overlay
   that makes humans cluster on round numbers (Solstad et al. 2026) shows up **strongly in
   Grok and not at all in Llama or Gemini**. The point where the model most resembles human
   *strategy* is the most variable across models.

### Relation to humans

The round-number anchoring we see in Grok is **not** a non-human quirk — humans do exactly
this. Solstad et al. (2026), using a near-identical 1–50 dot paradigm, find people estimate
by comparing to remembered references and partitioning, anchoring on round numbers
("I can't get away from my start-guess at 34"). So Grok's anchoring is a point of
*convergence* with human decision strategy, not a divergence. What the cross-model picture
adds is that this convergence is itself model-dependent.

### A separate finding: the count word gates the count (lexical effect)

In a companion run (mixed-shape stimuli, see the writeup), asking *"how many **dots**"*
makes models **exclude non-circular shapes from the count** — answering "there are no dots,
those are polygons" — while *"how many **shapes/objects**"* on the identical image recovers
the full count. The count noun's lexical category filters what gets counted: a language-layer
effect on number cognition, and the reason we use "objects" for the main estimation task.

## Notes and honest limits

- **Glance vs. enumerate.** Some instruct models compulsively serial-count at high N
  (enumerating past the true count, never giving a holistic estimate). Those cannot produce
  the analog "glance" regime this paradigm measures and were excluded; the three models here
  were confirmed to glance. A *reasoning*-mode model, by contrast, switches to a count-list
  procedure and largely defeats the Weber curve (accurate with little variance well past the
  subitizing range) — consistent with the human analog-vs-count-list distinction.
- **Coefficient of variation.** Error grows with magnitude (Weber's law is present), but the
  CV is not a clean flat constant the way idealized human analog data is; it wobbles and, in
  Grok, is distorted by round-number snapping. We report the curve honestly rather than
  forcing a constant-CV fit.
- **Small-model tier.** All three are small/cheap models. Whether precision keeps improving
  and whether anchoring emerges at frontier scale is open.
- **Scoring is by reading**, with notes on every ambiguous case in each model's
  `AI_READ_answers.md`. The `results.csv` `guess` column is a rough regex and is not trusted.

## Files

```
number-sense/
├── gen_stimuli.py      # deterministic dot-array generator (PIL)
├── run_experiment.py   # collect-only API harness (keys from env; raw -> JSONL)
├── stimuli/            # 160 PNGs + manifest.csv (ground-truth counts)
└── data/
    ├── grok-4.20-nonreasoning/   raw.jsonl · results.csv · AI_READ_answers.md
    ├── llama-3.2-11b-vision/     raw.jsonl · results.csv · AI_READ_answers.md
    └── gemini-2.5-flash-lite/    raw.jsonl · results.csv · AI_READ_answers.md
```

## How to reproduce

```bash
# regenerate the exact stimulus set (bit-for-bit from seed)
python3 gen_stimuli.py --sizes 1,2,3,4,5,6,7,8,9,10,12,15,20,25,30,40 --reps 10 --types A --seed 71 --out stimuli

# run one model (example; reads OPENROUTER_API_KEY / XAI_API_KEY from env)
python3 run_experiment.py --provider openrouter --model google/gemini-2.5-flash-lite \
    --objects-only --stim stimuli --out data/gemini-2.5-flash-lite --reps 5

# then READ data/<model>/raw.jsonl and score by reading (see ../PROTOCOL.md)
```

## References

- Gordon, P. (2004). Numerical cognition without words: evidence from Amazonia. *Science* 306:496–499.
- Solstad, T., Kaspersen, E., Romijn, E. I., & Hodgen, J. (2026). Decision-level processes in rapid numerosity estimation. *Cognition* 273:106511. (CC-BY)
- Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: heuristics and biases. *Science* 185:1124–1131.
- Whalen, J., Gallistel, C. R., & Gelman, R. (1999). Nonverbal counting in humans. *Psychological Science* 10:130–137.
