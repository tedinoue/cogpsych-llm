# Protocol — segmented sequential counting + interference

Follows the repository-wide rule in [`../PROTOCOL.md`](../PROTOCOL.md): **scripts collect
raw responses; a reader scores by reading.** This study adds a stricter clause — *no
extractor at all*, not even a convenience `guess` column — because during analysis a regex
misread a model's enumeration ("In Image 1… In Image 2…") as the counts `[1,2,3,4]` and
produced a false "non-faithful" flag; reading the transcript corrected it. Every number
reported here was read off the raw transcript by a reader, never parsed.

## Stimuli

- **Segments by construction, not by cutting.** Each sub-image is rendered as its own small
  PNG with an internal margin, so no dot can straddle a boundary. Ground truth is recorded at
  both levels (per-segment count and total) in `manifest.csv`.
- **One fixed cell: total = 24, 4 segments (T24/K4).** Per-segment counts are non-even (to
  defeat an equal-split shortcut) and capped at ≤9. No parametric sweep — the study answers
  one question (does an interceding task disrupt the carry), a within-configuration contrast.
- **Non-verbal stimuli: abstract glyph pairs.** Procedurally generated, semantically empty
  symbols (no letter/digit/icon), rendered tiny (≈64px, a few image tokens — comparable in
  input mass to a dot image, so the non-verbal arm doesn't differ in token weight). Each pair
  is "same" (identical glyph) or "different" (multiple strokes changed); balanced 50/50.
- **Deterministic.** Everything derives from one integer seed; the set regenerates
  bit-for-bit. Stimulus PNGs are not committed (regenerate them); the manifest and raw
  responses are.

## Procedure (multi-turn; the transcript is the memory)

1. **Instruction turn (once).** States both jobs: count the dots in each dot-image; do the
   arm's interleaved task each time it appears; the total will be asked at the end. For the
   non-verbal arm this is the *only* place the same/different task is described — its turns
   are thereafter bare images.
2. **Per dot-image:** "Image i:" + the image → the model states a count.
3. **Interleaved task turn** (all arms except control): the verbal arms send text (the load);
   the non-verbal arm sends a bare glyph-pair image, no text.
4. **Final turn:** "What is the total number of dots across all the dot-images?"

Prior per-image counts remain in the transcript throughout — deliberately. The experiment is
about interference, not memory; there is no hidden buffer to ablate. Degradation, if any, is
legible in the transcript.

## Arms

`control` (no interleave) · `v-num` (two-digit addition; sums kept >40 and ≠24 so the
interferer's answer can't be confused with the dot total) · `v-lang` (continue a neutral,
non-numeric sentence) · `v-desc` (describe the previous dot-image without a number;
*exploratory* — forces re-attention, so not load-bearing) · `nv` (same/different on a glyph
pair, no per-turn text — the non-verbal baseline).

## Manipulation check

We do not score the interferer's correctness; specific answers don't matter for the carry
question. We need only *evidence of engagement* so a null reads as "no interference," not
"the model skipped the task." Every interleaved reply is logged and tagged; a reader confirms
each arm's interleaved turns produced on-task output.

## Read-out (pre-registered)

- **Primary — faithful-adder / carry break:** does the final total equal the sum of the
  model's *own* stated per-image counts? A miscount that sums faithfully is not a disruption.
  Threshold: a verbal arm "disrupts" only if its carry-break rate is **≥ 15 points above the
  non-verbal arm's** (NV-relative — nets out generic interruption).
- **Secondary / descriptive — per-image counting accuracy** (NV-relative, ≥10-point drop):
  retained as a descriptive number, *not* the target. Dense-image undercounting is model
  counting-noise present in every arm and both thinking modes.
- **Statistics, honestly:** these are proportions; compare arms with a two-proportion test
  (Fisher's exact for the per-session carry-break rate). n = 30 per arm is a decision rule to
  *escalate* (collect more at the same cell — that's power, not scope creep), not a
  significance claim. A true null is a real, reportable result.

## Thinking modes

Gemini Flash-Lite defaults to thinking *off*. Run both: the default harness sends no thinking
config; the `_thinking` harness sends a thinking budget and captures the reasoning trace
(`thoughts`) in the raw record. The ≤9 per-segment cap was premised on near-exact counting,
which is a reasoning-model property — but dense-image undercounting appears in both modes, so
the cap does not fully isolate counting from carry; the faithful-adder check (carry vs. the
model's *own* counts) is what cleanly isolates the carry regardless.

## Honesty boundaries

Within-LLM characterization, not a human parallel; no online/temporal/recruitment language
(no decaying trace — the transcript is the memory); no mechanism-from-variance-signature; a
scattered/no-pattern result licenses nothing. Pushing load harder tests context-*retrieval*
over distance, a different mechanism from working-memory interference — not to be relabeled
"interference."
