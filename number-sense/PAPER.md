# Number Sense in Vision-Language Models: Subitizing, Weberian Estimation, and Model-Specific Round-Number Anchoring

*Ted Inoué, with the Solebury Mountain Research Collective*
*Working paper — data and code: github.com/tedinoue/cogpsych-llm*

---

## Abstract

We ran a classic human numerosity-estimation paradigm on vision-language models, asking not
whether they can count but what the *shape* of their number cognition is, and whether it matches
the human profile. Across three models from three independent labs (xAI's Grok, Meta's Llama,
Google's Gemini), a coarse human signature replicates: near-exact performance on small sets
(subitizing) gives way, above ~4 items, to estimation whose error grows with the number being
judged (Weber's law). The fine structure, however, is model-specific. Only one model (Grok)
subitizes perfectly; estimation precision tracks model capability; and most strikingly,
**round-number anchoring** — a documented human estimation strategy in which responses cluster on
multiples of five — appears strongly in Grok and is essentially absent in Gemini and Llama. We
demonstrate the anchoring result with a dedicated test covering every integer from 25 to 40, where
Grok's single most-common answer remains locked on "25" across true counts from 25 through 35
before stepping discretely upward. We conclude that the analog magnitude system (subitizing plus
magnitude-scaled error) is architecture-general, while its precision and the human-like
decision-strategy overlay that sits on top of it are model-specific. All raw model responses are
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
  and (in Grok) is distorted by round-number clustering (§4).
- **Precision tracks model quality.** Gemini, the strongest of the three small models, produces
  the tightest estimates and never fails. Llama, the weakest, is the noisiest and occasionally
  breaks down (refusals, garbled output, wild outliers). The analog system appears universal; its
  *precision* is capability-dependent.
- **Systematic under-estimation at high N.** All three under-count large sets, the gap widening
  with N — a compression also seen in humans.

The basic number-sense shape thus appears across three independent architectures and vendors; it
is not an artifact of any one lab's model.

## 4. Results: round-number anchoring is model-specific

The Weber experiment alone cannot test for round-number anchoring, because its high-N set sizes
(15, 20, 25, 30, 40) are themselves mostly round: a model is almost never shown a non-round
quantity in the range where rounding would surface. We therefore ran a dedicated test over **every
integer from 25 to 40**, interleaving round anchors (25, 30, 35, 40) with non-round fillers.

The clean diagnostic is the **modal response** — the single most common answer at each true count.
If a model anchors, its most likely answer stays "stuck" on a round value as the true count
changes, producing a flat *staircase* when modal response is plotted against true count. If a model
estimates honestly, its modal response climbs with the true count, producing a *diagonal*. (We
avoid leaning on "percent of answers that are multiples of five," because at a true count of 25 the
answer "25" is also simply correct; that metric conflates anchoring with accuracy.)

The three models dissociate sharply:

| Model | Anchors? | Modal response, true counts 25 → 40 |
|---|---|---|
| **Grok** (xAI) | **Yes, strongly** | locked on **25** from true 25 through 35, then steps to 32, then 40 — a staircase |
| **Gemini** (Google) | No | climbs with the true count — a diagonal |
| **Llama** (Meta) | No | climbs with the true count (noisy; mild stickiness near 40) — a diagonal |

Grok's anchoring is dramatic: its single most likely answer does not move across an eleven-unit
range of true counts (25 through 35). The mean creeps upward over that range only because a
minority of non-"25" responses drags the average along; the *mode* — the model's go-to answer — is
flat. Gemini and Llama, by contrast, track the true count with no round-number lock-on. All three
under-estimate, but only Grok rounds.

Round-number anchoring — a documented *human* estimation strategy, and thus a point of potential
convergence between model and human cognition — therefore appears strongly in one frontier model
and is absent in two others. It is not a universal property of vision-LLM number estimation. It
belongs to each model's particular profile.

## 5. Discussion

Two layers separate cleanly in these data. The **analog magnitude layer** — subitizing followed by
magnitude-scaled estimation error — is shared across all three models and matches the human core
number sense in shape. The **decision-strategy layer** that humans lay on top of the analog
estimate — comparison to references, partitioning, and round-number anchoring — is *model-specific*:
it is pronounced in Grok and largely absent in Gemini and Llama.

This maps onto a useful framing of human numerical cognition itself, in which a shared, evolutionarily
old analog system is augmented by learned, language-mediated procedures. The models appear to
reproduce the analog layer near-universally while differing in which human-like decision strategies,
if any, they have acquired. We summarize this as each model having its own "numerical personality":
the broad number-sense shape is convergent, the fine structure is not.

A note on the round-number result and human comparison: it would be a mistake to read Grok's
anchoring as a *non-human* quirk. Humans anchor on round numbers in exactly this paradigm. Grok's
anchoring is, if anything, a point of convergence with human decision strategy — and what the
cross-model picture adds is that this convergence is itself model-dependent, present in some systems
and not others.

*A casual, non-load-bearing observation, offered only as a direction for future work and not as a
finding:* in separate, earlier color-perception work, the same model (Grok) tended to hold a
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
or produce ranges and refusals. A regex that reduces all of this to a single integer produces
*unreliable data*, not merely unreliable analysis — and does so silently. In the course of this work,
an automated parser turned a *correct* high-count answer into a fabricated "catastrophic collapse"
by grabbing a digit out of the model's enumeration list; the error was invisible until the raw
responses were read.

The harness therefore writes every full response to disk, and analysis is performed by reading.
This repository publishes all raw responses so that any reader can re-score them. The visualization
scripts operate only on the human-read answer values, never on raw model output.

We also note, frankly, that several of this study's conclusions were revised after human review of
the model's own confident summaries: an apparent "collapse" that was a parsing artifact; an initial
reading of round-number clustering as non-human that the human literature corrected to a
convergence; and a premature "absent in other models" claim about anchoring that had in fact never
been tested until the dedicated experiment of §4 was run. The analysis pipeline's human-in-the-loop
review step changed the conclusions, and we regard that as a feature of the method rather than an
embarrassment to be hidden.

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
