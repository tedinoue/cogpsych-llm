# cogpsych-llm

Running classic cognitive-psychology paradigms on large language models.

This repository holds experiments that take well-established paradigms from human
cognitive psychology and run them, unchanged in spirit, on vision- and language-model
systems — to ask where machine cognition *converges* with the human profile and where it
*diverges*. The aim is not "can the model do the task" (a benchmark question) but "what is
the *shape* of the model's cognition, and does it match the human shape?"

The work here supports a larger study on language and the structure of thought (a
strong–Sapir-Whorf / emergent-world-model argument); these are its empirical sub-studies.

## Studies

| Study | Question | Status |
|-------|----------|--------|
| [`number-sense/`](number-sense/) | Do vision-LLMs show the human numerosity-estimation signature — subitizing, Weber's law, and the decision-strategy overlay (round-number anchoring)? | Data released; writeup in progress |
| [`segmented-counting/`](segmented-counting/) | Does verbal interference disrupt an LLM's running count the way it disrupts human exact counting (Frank et al. 2012)? | Data released; clean null — and a methodological point: interference paradigms read out the *maintenance substrate*, which an LLM's context window doesn't share with humans |

More sub-studies will be added as the larger paper develops.

## Method note (important)

These experiments follow one methodological rule, documented in
[`PROTOCOL.md`](PROTOCOL.md): **scripts collect raw model responses; a human/AI reads and
scores them.** Automated parsing of model output is unreliable beyond the most trivial
cases (a model that answers "1 dot top-left, 1 medium dot... total 18" defeats a
regex that grabs "the number"). Every reported result here was scored by *reading* the raw
responses, which are all published so anyone can re-score them.

## Reproducibility

Every study ships its stimulus generator, its collect-only run harness, the exact stimulus
images, and every model's raw responses (`raw.jsonl`). Stimuli are generated
deterministically from a seed, so the image set can be regenerated bit-for-bit. API keys
are never committed; the harness reads them from the environment.

## License

- **Code** (`*.py`): MIT — see [`LICENSE`](LICENSE).
- **Data, stimuli, figures, and writeups**: CC-BY-4.0 — see [`LICENSE-DATA`](LICENSE-DATA).

If you use the data or findings, please cite this repository.

## Authorship

Ted Inoué, with the Solebury Mountain Research Collective. Experiments designed and run
collaboratively; analysis performed by reading model responses per the protocol above.
