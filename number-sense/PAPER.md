# Number Sense in Vision-Language Models: Subitizing, Weberian Estimation, and Round-Number Anchoring

*Ted Inoué, with the Solebury Mountain Research Collective*
*Working paper — data and code: github.com/tedinoue/cogpsych-llm*

---

## Abstract

We ran a classic human numerosity-estimation paradigm on vision-language models, asking not
whether they can count but what the *shape* of their number cognition is, and whether it matches
the human profile. Across three models from three independent labs (xAI's Grok, Meta's Llama,
Google's Gemini), a coarse human signature replicates: near-exact performance on small sets gives
way, above ~4 items, to estimation whose absolute error grows with the number being judged. The
fine structure varies by model. One model (Grok) is exact across the small-set range; the three
differ in estimation precision; and **round-number anchoring** — a documented human estimation
pattern in which responses cluster on multiples of five — appears in **all three** models, varying
markedly in strength. We demonstrate the anchoring with a dedicated test covering every integer from
25 to 40: each model's most-common answer locks onto preferred values and holds them across runs of
consecutive true counts (a staircase), Grok most extremely (its mode remains "25" across true counts
25 through 35), Gemini and Llama more mildly (modal plateaus of about four counts on values such as
26, 30, and 40). The human-like estimation profile (small-set exactness, magnitude-scaled error,
round-number anchoring) is present in every model we tested, and the anchoring is shared in kind
while differing sharply in degree. We hold the underlying-mechanism question open: these are behavioral
matches to the human profile, and we note where a model account (a learned round-number output prior;
precision-weighted inference) could produce the same pattern without a dedicated "number system." All
raw model responses are published; every reported value was scored by reading the responses, with a
non-authoritative regex hint also present in the logs but never used (see §6).

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

## 3. Results: the estimation signature appears in every model tested

All three models show the coarse human signature: accurate on small sets, then estimation whose
absolute error grows with the number judged. We describe this in behavioral terms. The human terms
of art (an analog magnitude system, subitizing) name posited internal mechanisms; what we measure is
the output profile, and matched output does not by itself establish the human mechanism, a point we
return to in the discussion.

- **Small-set range.** Performance is best at the smallest counts. Only **Grok** is *exact* (zero
  variance, for 1–4); both Llama and Gemini make occasional errors even at counts of 2–4. (We call
  this small-set exactness rather than "subitizing," which in humans names a specific parallel
  individuation process with a reaction-time signature we did not measure.) Clean exactness at small
  counts is therefore the exception among these models,
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

Round-number anchoring is a documented *human* estimation pattern (anchoring-and-adjustment; the
clustering of numerosity estimates on round values — Tversky & Kahneman, 1974; Solstad et al.,
2026), and the same pattern in the models is a clear point of convergence with human behavior. Every
model we tested anchors, and they differ markedly in how wide the capture zones are and how strongly
the responses pile onto round values: shared in kind, model-specific in degree.

## 5. Discussion

Read behaviorally, two regularities appear in these data. The first is the estimation profile,
small-set exactness followed by magnitude-scaled error, present in all three models and matching the
shape of the human core number sense. The second is round-number anchoring, also present in all
three, with strength varying sharply by model: pronounced in Grok (wide capture zones, a majority of
answers on round values), milder in Gemini and Llama (short modal plateaus, bulk distributions only
just above chance). The same anchoring is documented in humans on this paradigm, so its appearance in
the models is convergence with human behavior, and we state that plainly.

The standard account of human number cognition reads these as two layers, an evolutionarily old
analog magnitude system augmented by learned, language-mediated decision strategies. The behavioral
match invites that framing, and we use it as the natural description. But we are measuring output, not
internal organization, and two more economical model-side accounts predict the same data without a
dedicated "number system," so we name them rather than assume the human mechanism. First, the
round-number clustering may be a property of the model's *output prior* over number tokens: round
counts ("about thirty," "roughly twenty-five") are over-represented in training text, so a language
model's distribution over number words is lumpy on multiples of five before any estimation strategy
is invoked. That alone predicts the anchoring. Second, both the estimation spread and the anchoring
strength may be one quantity seen from two sides: under a precision-weighted-inference reading, a
round-valued prior dominates when the perceptual read is imprecise and yields when it is sharp, which
predicts that the model with the looser estimation spread (Grok) should also anchor hardest and the
tightest (Gemini) least, the ordering we in fact observe. We do not adjudicate among the two-layer,
output-prior, and precision-weighting accounts here; the behavioral convergence with humans holds
under all three, and which mechanism underlies it is the question a follow-up should target. We
summarize the descriptive result as each model having its own "numerical personality": the broad
shape is convergent in kind, the degree of each feature is not.

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
only on the human-read answer values (the `AI_READ_answers.json` files), never on raw model output.

One point of exactness about the published data, since the claim above is strong. Each raw record
also carries a `guess` field produced by a naive last-integer regex. That field is exactly the kind
of automated extraction this section warns against; it exists only as a console progress-indicator
during collection, and no reported value in this paper or any figure was taken from it. The values
of record are in the `AI_READ_answers.json` files, transcribed and read by hand. We leave `guess` in
the released records rather than delete it, both because altering raw data after collection is itself
bad practice and because its disagreements with the read values, on the very responses where a model
narrates a count before committing to a total, are a useful illustration of why the regex cannot be
trusted. The `results.csv` table is generated alongside `guess` and should not be used for scoring;
the `AI_READ_answers.json` files are the data of record.

## 7. Limitations

- All three models are small/cheap-tier. Whether the estimation precision and the anchoring strength
  change at frontier scale is open.
- **The three models differ in vendor, parameter count, and release vintage at once, so n=3 cannot
  attribute the precision differences to any one of these.** We describe the precision differences;
  we do not claim they track "capability," which the design cannot isolate. Separating capability from
  size and vintage needs a within-family size ladder, which we did not run.
- We report absolute error growing with magnitude, not a fitted constant coefficient of variation:
  the CV is not cleanly constant, so we do not claim a formal Weber's-law fit. The high-N
  under-estimation conflates estimation compression with, in Grok's case, round-number snapping.
- Small-set exactness is reported from accuracy alone. Subitizing in humans is defined by a
  reaction-time signature; latency was logged but not analyzed for it, so we do not claim subitizing
  in the technical sense, only exactness at small counts.
- Three transformer vision-language models trained on overlapping web-scale data are three samples,
  not a sampling of architectures; "present in every model tested" is the claim, not invariance across
  architectures the study did not vary.
- Llama is the noisiest model (refusals, garble, outliers); its anchoring is present but its data are
  messy, and the noise partly reflects model capacity.
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
