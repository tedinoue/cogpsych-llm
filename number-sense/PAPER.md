# Number Sense in Vision-Language Models: Subitizing, Weberian Estimation, and Round-Number Anchoring

*Ted Inoué, with the Solebury Mountain Research Collective*
*Working paper — data and code: github.com/tedinoue/cogpsych-llm*

---

## Abstract

We ran a classic human numerosity-estimation paradigm on vision-language models, asking not
whether they can count but what the *shape* of their number cognition is, and whether it matches
the human profile. Across three models from three independent labs (xAI's Grok, Meta's Llama,
Google's Gemini), a coarse human signature replicates: near-exact performance on small sets
(subitizing) gives way, above ~4 items, to estimation whose error grows with the number being
judged (Weber's law). The fine structure varies by model. Only one model (Grok) subitizes
perfectly; estimation precision tracks model capability; and **round-number anchoring** — a
documented human estimation strategy in which responses cluster on multiples of five — appears in
**all three** models, varying markedly in strength. We demonstrate this with a dedicated test
covering every integer from 25 to 40: each model's most-common answer locks onto preferred values
and holds them across runs of consecutive true counts (a staircase), Grok most extremely (its mode
remains "25" across true counts 25 through 35), Gemini and Llama more mildly (modal plateaus of
about four counts on values such as 26, 30, and 40). We conclude that the analog magnitude system
(subitizing plus magnitude-scaled error) is architecture-general, and that the human-like
round-number-anchoring strategy is architecture-general in kind while differing in degree across
models; estimation precision, in turn, tracks model capability. All raw model responses are
published; every reported value was scored by reading the responses, not by automated parsing.

---

## 1. Background

Humans show a remarkably consistent profile when asked "how many?" for a set of objects:

1. **Subitizing.** Sets of roughly one to four are apprehended instantly and reported exactly,
   with no error and effectively no response-time cost.
2. **Analog estimation (Weber's law).** Above the subitizing range, people *estimate*, and the
   variability of their estimates grows in proportion to the quantity — a roughly constant
   coefficient of variation, the signature of an analog magnitude system. This system is shared
   across cultures, including peoples whose languages lack exact count words above two, who
   nonetheless show the same estimation signature as numerate adults (Gordon, 2004).
3. **Decision strategies on top.** For larger sets, people do not simply read off a magnitude;
   they compare the display to a remembered reference, partition it into parts and recombine, and
   **anchor their answers on round numbers**, adjusting away from a salient starting value
   (anchoring-and-adjustment; Tversky & Kahneman, 1974). A recent study using a near-identical
   1–50 dot paradigm documents these decision-level processes directly, with participants saying
   things like "I'm gonna say 20" and "I can't get away from my start-guess at 34" (Solstad,
   Kaspersen, Romijn & Hodgen, 2026).

Vision-language models now perform "how many?" tasks routinely. We treat that ability not as a
benchmark to be scored but as a behavior to be *characterized*: does a model's number cognition
have the human shape — subitizing, Weberian error growth, round-number anchoring — and where does
it diverge?

## 2. Method

**Stimuli.** Black filled circles on a white background, at exact known counts, scattered at
random non-overlapping positions. Individual dot sizes are jittered so that the total dark area
does *not* track the count (across the high-N range the total area plateaus and even declines),
preventing a model from substituting "more ink" for "more dots." Stimuli are generated
deterministically from a seed and are fully reproducible; the generator and a manifest of
ground-truth counts are included in the repository.

**Task.** A single neutral prompt — *"How many objects are in this image?"* — issued as fresh,
independent API calls with no shared conversation history, so that variation across repetitions
reflects the model rather than context carryover. (We deliberately avoid the word "dots." In a
companion observation, asking "how many *dots*" over mixed-shape displays causes models to exclude
non-circular shapes from the count — a lexical-category effect on number reporting — which is why
the estimation task uses "objects.")

**Models.** Three *non-reasoning* models, each confirmed in pre-flight to estimate at a glance
rather than serially enumerate (models that compulsively enumerate cannot produce the analog
"glance" regime this paradigm measures and were excluded):

- `grok-4.20-non-reasoning` (xAI)
- `llama-3.2-11b-vision-instruct` (Meta)
- `gemini-2.5-flash-lite` (Google)

**Scoring.** Every model response was logged verbatim, and the final committed answer was extracted
**by reading** each response, not by automated parsing. This is a deliberate methodological
commitment (see §6). Refusals and garbled outputs were recorded and excluded from the numeric
summaries with their counts noted.

**Two experiments.**

- *Weber curve* (§3): 16 set sizes (1–10, 12, 15, 20, 25, 30, 40), 10 layouts × 5 repetitions =
  50 calls per set size per model.
- *Anchoring test* (§4): every integer 25–40, 15 layouts × 15 repetitions = 225 calls per integer
  per model, designed specifically to separate round-number anchoring from accuracy.

## 3. Results: the analog signature is architecture-general

All three models show the coarse human signature: accurate on small sets, then estimation whose
absolute error grows with the number judged.

- **Subitizing range.** Performance is best at the smallest counts. Notably, only **Grok**
  subitizes *perfectly* (exact, zero variance, for 1–4); both Llama and Gemini make occasional
  errors even at counts of 2–4. Clean subitizing is therefore the exception among these models,
  not the rule.
- **Weberian error growth.** Above the subitizing range, the spread of responses widens with the
  true count — error scaling with magnitude, the analog-estimation signature. The coefficient of
  variation is present but is *not* a clean flat constant of the idealized human kind; it wobbles,
  and is distorted by the round-number clustering documented in §4.
- **Precision tracks model quality.** Gemini, the strongest of the three small models, produces
  the tightest estimates and never fails. Llama, the weakest, is the noisiest and occasionally
  breaks down (refusals, garbled output, wild outliers). The analog system appears universal; its
  *precision* is capability-dependent.
- **Systematic under-estimation at high N.** All three under-count large sets, the gap widening
  with N — a compression also seen in humans.

The basic number-sense shape thus appears across three independent architectures and vendors; it
is not an artifact of any one lab's model.

## 4. Results: round-number anchoring is general, and varies in strength

The Weber experiment alone cannot test for round-number anchoring, because its high-N set sizes
(15, 20, 25, 30, 40) are themselves mostly round: a model is almost never shown a non-round
quantity in the range where rounding would surface. We therefore ran a dedicated test over **every
integer from 25 to 40**, interleaving round anchors (25, 30, 35, 40) with non-round fillers.

The clean diagnostic is the **modal response** — the single most common answer at each true count.
If a model anchors, its most likely answer stays "stuck" on a value across a run of consecutive
true counts, producing a *staircase* when modal response is plotted against true count: flat treads
on preferred values, with discrete steps between them. If a model estimated without any preferred
values, its modal response would climb smoothly with the true count (a diagonal).

**All three models produce staircases, not diagonals.** Each one's modal answer locks onto a value
and holds it across a run of true counts before stepping. Their modal sequences (true count 25 → 40):

- **Grok:** 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 32, 32, 40, 40, 40
- **Gemini:** 25, 26, 26, 26, 26, 30, 30, 30, 30, 31, 30, 33, 35, 35, 36, 36
- **Llama:** 20, 25, 28, 23, 27, 30, 31, 30, 30, 33, 36, 39, 40, 40, 40, 40

Gemini's mode holds at ~26 across true counts 26–29, then locks on **30** across 30–33, then climbs
in steps and reaches only 35–36 even when the true count is 40. Llama, noisier, bounces near 25 for
25–29, sticks near **30** for 30–33, then climbs and locks on **40** for the top four. Grok shows the
same behavior in extreme form.

Three quantitative measures (true counts 25–40; for a non-anchoring estimator, chance gives a modal
multiple-of-five at ~4/16 and ~20% of all answers on a multiple of five):

| Measure | Grok (xAI) | Gemini (Google) | Llama (Meta) |
|---|---|---|---|
| True counts whose **mode is a multiple of 5** | **14 / 16** | 8 / 16 | 9 / 16 |
| Widest **capture zone** (consecutive true counts sharing one locked mode) | **11** (value 25) | 4 (values 26, 30) | 4 (value 40) |
| Share of **all** answers on a multiple of 5 | **55 %** | 25 % | 26 % |

The pattern is consistent across all three labs: round-number/value anchoring is present in every
model, manifesting as modal plateaus that lock onto preferred values and step between them. What
differs is **strength**. Grok is extreme — its mode holds the value 25 across eleven consecutive
true counts, nearly all of its modal answers are multiples of five, and a clear majority (55%) of
*all* its responses are multiples of five, far above the ~20% chance baseline. Gemini and Llama are
milder: their overall multiple-of-five rates sit only just above chance (25–26%), but their *modal*
answers nonetheless lock into round plateaus (four-count treads on 26, 30, and 40), which is the
anchoring signature appearing in the mode even when the bulk distribution looks near-chance.

Round-number anchoring is a documented *human* estimation strategy (anchoring-and-adjustment; the
clustering of numerosity estimates on round values — Tversky & Kahneman, 1974; Solstad et al.,
2026), and is thus a point of convergence between model and human cognition. Our data indicate this
convergence is **architecture-general in kind but model-specific in degree**: every model anchors,
and they differ markedly in how wide the capture zones are and how strongly the responses pile onto
round values.

## 5. Discussion

Two layers appear in these data. The **analog magnitude layer** — subitizing followed by
magnitude-scaled estimation error — is shared across all three models and matches the human core
number sense in shape. The **decision-strategy layer** that humans lay on top of the analog
estimate — comparison to references, partitioning, and round-number anchoring — also appears across
all three, but its *strength* varies sharply by model: pronounced in Grok (wide capture zones, a
majority of answers on round values), milder in Gemini and Llama (short modal plateaus, bulk
distributions only just above chance).

This maps onto a useful framing of human numerical cognition itself, in which a shared, evolutionarily
old analog system is augmented by learned, language-mediated procedures. The models reproduce the
analog layer near-universally and also exhibit the round-number-anchoring strategy near-universally,
differing in how strongly that strategy is expressed. We summarize this as each model having its own
"numerical personality": the broad shape is convergent in kind, the degree of each feature is not.

A note on the round-number result and human comparison: it would be a mistake to read this
anchoring as a *non-human* quirk. Humans anchor on round numbers in exactly this paradigm. The
models' anchoring is, if anything, a point of convergence with human decision strategy — and what
the cross-model picture adds is that the *degree* of this convergence is model-dependent.

*A casual, non-load-bearing observation, offered only as a direction for future work and not as a
finding:* in separate, earlier color-perception work, one of these models (Grok) tended to hold a
canonical reference value — a named color, "school-bus yellow," cited to a standard — against a
gradually shifting perceptual input longer than other models, and to manufacture precise-sounding
reference values when pressed. Whether this loosely resembles the number-anchoring behavior, and
whether either reflects something specific about how the model was trained, cannot be settled here;
a dedicated cross-paradigm, same-generation study would be required to make any such claim. We note
it only as a possibility worth examining.

## 6. A note on methodology: scripts collect, humans read

Every numeric result above was obtained by **reading** the model responses, not by extracting
answers with a script. This is deliberate. Automated extraction of "the answer" from a
language-model response is unreliable for anything beyond the most trivial outputs: models narrate
a count before committing to a total, self-correct mid-response, answer in an unexpected register,
or produce ranges and refusals. A regular expression that reduces all of this to a single integer
can silently produce *unreliable data*, not merely unreliable analysis — for example by grabbing a
digit out of an enumeration list rather than the final committed total.

The harness therefore writes every full response to disk, and analysis is performed by reading those
responses; the answer-extraction is done by a human reader, with every ambiguous case (self-
corrections, ranges, refusals) adjudicated explicitly and recorded. This repository publishes all
raw responses so that any reader can re-score them independently. The visualization scripts operate
only on the human-read answer values, never on raw model output.

## 7. Limitations

- All three models are small/cheap-tier. Whether estimation precision keeps improving, and whether
  anchoring emerges, at frontier scale is open.
- One prompt, one session per condition. Robustness to prompt variation is untested here.
- The coefficient of variation is reported as observed rather than fit to a constant-CV model; the
  high-N under-estimation conflates genuine estimation compression with, in Grok's case,
  round-number snapping.
- Llama's noise (refusals, garble, outliers) partly reflects model capacity, not only a different
  number sense; its "tracking" classification is robust but its data are messy.
- Scoring by reading, while more reliable than parsing for this material, is not blinded; the
  per-response judgments and every ambiguous case are published for audit.

## References

- Gordon, P. (2004). Numerical cognition without words: Evidence from Amazonia. *Science*,
  306(5695), 496–499.
- Solstad, T., Kaspersen, E., Romijn, E. I., & Hodgen, J. (2026). Decision-level processes in rapid
  numerosity estimation. *Cognition*, 273, 106511. (Open access, CC-BY.)
- Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science*,
  185(4157), 1124–1131.
- Whalen, J., Gallistel, C. R., & Gelman, R. (1999). Nonverbal counting in humans: The psychophysics
  of number representation. *Psychological Science*, 10(2), 130–137.

---

*Data, stimuli, raw model responses, and analysis code: github.com/tedinoue/cogpsych-llm.
Code under MIT; data, figures, and text under CC-BY-4.0.*
