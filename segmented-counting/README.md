# Segmented sequential counting, and interference

**A short study with a methodological point bigger than its result.**

This experiment ports a classic verbal-interference paradigm — the kind used to show that
human exact counting depends on language (Frank et al. 2012, articulatory suppression) —
onto a vision-language model. The result is a clean **null**: no interleaved task disrupts
the model's running count. The point is *why* that null is not a failure but a finding, and
what it says about running human cognitive-psychology experiments on LLMs at all.

## The headline (read this first)

**Classic working-memory / dual-task / interference paradigms presuppose a short-term store
that is limited, actively maintained, and *shared* between the task and the interfering
load. The LLM context window is none of those things. So when these paradigms are
transplanted to an LLM, a null result does not mean the cognitive property is absent — it
means the paradigm's *enabling mechanism* is absent.**

Before comparing a human and an LLM with any classic experiment, you have to ask whether the
experiment's logic depends on an architectural feature the LLM lacks. This study is the
worked example: interference-on-counting reads out the *maintenance substrate*, and the
LLM's substrate (an immutable transcript) is constitutionally different from the human's
(a fragile, overwritable verbal loop). The paradigm cannot produce the dissociation it was
built to find. The absence of an effect is closer to a **category error** — the question
presupposes a mechanism the system doesn't have — than to a null.

## The question

In humans, *verbal* interference (but not a matched *non-verbal* load) knocks exact counting
down to approximate estimation. This is a central piece of evidence that language is
recruited online for exact number — that the count is held in a verbal rehearsal loop, and
occupying that loop corrupts it.

The LLM analog: present a total split across several sub-images, one per turn, and ask for
the total at the end. Between the image turns, interleave a task. Does a **verbal**
interleaved task degrade the running count more than a matched **non-verbal** one?

A framing note we hold throughout: this is a **within-LLM characterization, not a
human-parallel claim**. There is no temporal "online" buffer to occupy — the transcript
*is* the memory. We do not import "online recruitment" or trace-decay language.

## Design

One fixed cell — total = 24 dots, split across 4 sub-images (T24/K4), non-even splits, each
sub-image capped at ≤9 dots. No parametric sweep; the study answers one question (does an
interceding task disrupt the carry), which is a within-configuration contrast, so the only
thing that varies across arms is the *interference*.

Five arms, each a genuine multi-turn session (instruction once at the start; then per turn:
a dots image → the model's count; then the interleaved task → the model's response; finally
"what's the total?"):

| Arm | Interleaved task | Channel |
|-----|------------------|---------|
| **control** | none | — |
| **v-num** | a two-digit addition ("47 + 38") | verbal / number |
| **v-lang** | continue a sentence (non-numeric) | verbal / language |
| **v-desc** | describe the previous dot-image, no number *(exploratory)* | verbal, about-the-count |
| **nv** | same/different on a pair of tiny abstract glyphs, **no per-turn text** | non-verbal / visual |

Design choices that matter:

- **No difficulty-matching.** Frank matched difficulty to control for a *shared depleting
  resource pool*. An LLM has no such pool — each turn is a fresh forward pass over the whole
  transcript; nothing depletes across turns. "Was the verbal task harder" is not the
  confound here; *what channel it occupies* is the variable. The non-verbal arm — a real
  interleaved task of comparable presence — is the control for "does *any* interruption
  disrupt," by construction, without a difficulty staircase.
- **The non-verbal arm carries no per-turn text.** Any per-turn prompt would inject the
  verbal channel into the supposedly non-verbal task. The same/different instruction is given
  once, at the start; thereafter the glyph turns are bare images and the model routes on
  content. (The verbal arms *do* carry per-turn text — that asymmetry is the manipulation,
  not a confound: per-turn text occupying the verbal channel *is* the verbal load.)
- **Abstract glyphs, not emoji.** The non-verbal stimuli are procedurally generated,
  semantically empty symbols — no letter, digit, or icon. A recognizable emoji, even shown
  as an image, may route to a rich semantic/linguistic representation and smuggle language
  through the visual door; an abstract glyph has no concept to route to, so same/different
  must be judged on visual form. (Whether a pictured emoji *does* engage the verbal channel
  is an interesting question — a separate experiment, not this control.)
- **Both thinking modes.** Gemini Flash-Lite defaults to thinking off; we ran the experiment
  with thinking off (complete) and with thinking on (partial — see below).

## Read-out

The primary read-out is the **faithful-adder** check: does the final total equal the sum of
the model's *own* stated per-image counts? A miscount that propagates faithfully into the
total is *not* a disruption — it's a vision-counting slip, equal across arms. Disruption
would be the total **diverging from the model's own counts** because an interleaved task
knocked the running tally loose. That divergence is the thing an interference effect would
produce, and it is what we measure, NV-relative (a verbal arm "disrupts" only if it does so
*more* than the non-verbal arm of comparable presence).

All scoring is done by **reading the raw responses** — no parser, no regex, no extracted
"guess" column anywhere (see [`../PROTOCOL.md`](../PROTOCOL.md); in this study even the
convenience extractor is omitted, because a regex misread enumeration labels as counts and
produced a false result during analysis — corrected by reading).

## Results

### Thinking-off — complete, 5 arms × 30 sessions

Faithful-adder rate (total matches the sum of the model's own per-image counts):

| Arm | Faithful-adder | Carry breaks |
|-----|----------------|--------------|
| control | 29 / 30 | 1 |
| v-num (arithmetic) | 29 / 30 | 1 |
| v-lang (sentence) | **30 / 30** | 0 |
| v-desc (describe) | **30 / 30** | 0 |
| nv (non-verbal baseline) | 28 / 30 | 2 |

**No verbal arm disrupts the carry.** The pre-registered threshold — a verbal arm's carry-
break rate ≥ 15 points *above* the non-verbal baseline — is met by none of them. The verbal
arms are at or *below* the non-verbal baseline. The four carry breaks across 150 sessions
fall in the control, arithmetic, and non-verbal arms — the *non-pure-verbal* conditions —
and are absent from the two pure verbal arms. If anything, the carry is slightly noisier
*without* verbal interference, the opposite of the human pattern. **Clean null.**

(Per-image counting itself is ~88% at this dot density — off-by-one undercounts on the
densest 8–9-dot images — in *both* thinking modes and in the control. That is model
counting-noise, equal across arms, not an interference effect. The faithful-adder check nets
it out: the model reliably sums whatever it counted.)

### Thinking-on — partial (3 of 5 arms), corroborating

control, v-num, and v-lang each completed 30 sessions, all faithful — the same null.
v-desc (n = 5) and the nv baseline (n = 0) were **not collected**: a sustained provider
outage (HTTP 503 storm) made thinking-on collection — which is heavier per session — stall,
and we stopped rather than spend hours on confirmatory data. The full-n claim therefore
rests on the complete thinking-off dataset; thinking-on is corroboration.

Thinking-on makes the underlying point *more* legible: with reasoning on, the model writes
the running total into the transcript explicitly after every image ("3 + 7 = 10 so far"). It
actively re-commits the count to the immutable record each turn — the substrate point shown,
not argued. The nv-thinking baseline can be topped up later (the harness resumes and skips
completed sessions); the conclusion holds without it, since the thinking-off non-verbal arm
was already the *noisiest* and no verbal arm exceeded it.

## What it means

Both human and LLM hold number in a linguistically formatted representation. The difference
the interference paradigm exposes is not *format* but *substrate*:

- **Human:** number is held in a fragile, serial, overwritable verbal loop. Occupy the loop
  and the count degrades. Interference works because format and maintenance are *fused* in
  one fragile mechanism.
- **LLM:** number is written into an immutable, parallel transcript and re-read each forward
  pass. There is no fragile buffer to occupy. Interference has nothing to grab.

So the null does **not** refute linguistic formatting of number in LLMs. It shows that
interference paradigms read out the *maintenance substrate*, and that the LLM's substrate is
constitutionally different. The same "number is linguistic" thesis predicts *opposite*
interference results in the two systems — because the linguistic substrates have opposite
fragility properties. This is a lawful cross-architecture divergence with a mechanistic
reason; it is not "the LLM is better," and it is not evidence the LLM's number isn't
language-shaped.

And it generalizes: any classic paradigm whose logic rests on a limited, actively-maintained,
shared store should be screened for substrate-dependence before it is run on an LLM and
before its result is compared to humans.

## Honest limits

- One model (Gemini 2.5 Flash-Lite), one fixed cell. Cross-model and cross-architecture
  replication is needed before the divergence is asserted as general; it is the next step.
- Thinking-on is partial (no non-verbal thinking baseline).
- A null at this load does not show the count is *unconditionally* incorruptible. Pushing
  much harder (many tasks per gap; burying the count under long context; confusable
  values in the count's range) might degrade *retrieval over distance* — but that is a
  context-window property, a different mechanism from working-memory interference, and would
  be a different study. We do not call it "interference."
- The v-desc arm is exploratory: asking the model to describe the just-counted image forces
  re-attention to that image, so a v-desc effect would be ambiguous between verbal-channel
  interference and re-counting. It is not load-bearing for the headline.

## Files

- [`gen_segmented_stimuli.py`](gen_segmented_stimuli.py) — dot-segment stimulus generator
  (deterministic from a seed; T24/K4).
- [`gen_glyph_pairs.py`](gen_glyph_pairs.py) — abstract glyph same/different pairs for the
  non-verbal arm.
- [`run_segmented_experiment.py`](run_segmented_experiment.py) — the multi-turn collection
  harness (thinking-off / default), raw-only, retry + resume.
- [`run_segmented_experiment_thinking.py`](run_segmented_experiment_thinking.py) — the
  thinking-on variant (sends a thinking budget, captures the reasoning trace).
- [`data/`](data/) — every model's raw responses (`raw.jsonl`), by thinking mode and arm.
  This is the irreplaceable artifact; re-score it by reading.
- [`PROTOCOL.md`](PROTOCOL.md) — the full segmented-count + interference protocol.

## How to reproduce

```bash
# regenerate the exact stimulus set (bit-for-bit from seed)
python3 gen_segmented_stimuli.py --grid --reps 30 --seed 2026 --out stimuli
python3 gen_glyph_pairs.py --n 60 --seed 2026 --out glyph_pairs

# run one arm (reads GEMINI_API_KEY from env; thinking-off)
python3 run_segmented_experiment.py --arm v-num \
  --stimuli stimuli --glyphs glyph_pairs --out data/gemini-2.5-flash-lite/v-num --resume

# then READ data/<mode>/<arm>/raw.jsonl and score by reading (see ../PROTOCOL.md). Do not parse.
```

## References

- Frank, M. C., Fedorenko, E., Lai, P., Saxe, R., & Gibson, E. (2012). Verbal interference
  suppresses exact numerical representation. *Cognitive Psychology*, 64(1–2), 74–92.
- Companion study in this repo: [`../number-sense/`](../number-sense/) — the numerosity-
  estimation signature in vision-LLMs.
