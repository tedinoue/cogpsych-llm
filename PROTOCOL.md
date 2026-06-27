# Methodology protocol

## Scripts collect; humans/AI analyze

The single binding rule for every experiment in this repository:

> **Scripts collect raw model responses. They do not parse, score, or aggregate them.
> A reader (human, or an AI reading the responses) does all scoring and interpretation.**

### Why

Automated extraction of "the answer" from a language model's response is unreliable for
anything but the most trivial outputs. Models routinely:

- narrate a count before answering ("1 dot top-left, 1 medium dot below... a total of 18") —
  a regex that takes the first integer returns **1**, not 18;
- self-correct mid-response ("7 shapes... wait, looking again, 8 shapes total");
- answer in a register the parser doesn't expect ("none of these are *dots* — they're
  polygons", which is a meaningful answer, not a failure);
- refuse, hedge, or produce a range.

A script that reduces all of this to a single extracted integer produces **unreliable data**,
not merely unreliable analysis — and it does so silently. In our own runs, a regex turned a
*correct* high-count answer ("Final answer: 18") into a fake "catastrophic collapse" by
grabbing a digit out of the model's enumeration list. The error was invisible until the raw
responses were read.

So: the harness writes the full verbatim response to `raw.jsonl` for every call, and the
analysis is done by reading those responses. The `results.csv` includes a convenience
`guess` column produced by a rough regex — it is a progress indicator only and is **not**
the basis of any reported result. Treat it as untrusted.

### What this means for reuse

Every `raw.jsonl` here contains the complete model responses. If you want to re-score the
data with a different criterion (or audit ours), read the raw responses — don't trust an
extracted number, ours or your own regex's. The `AI_READ_answers.md` file in each model's
data folder records the final answers as scored by reading, with notes on every ambiguous
or self-correcting case.

## Other conventions

- **Deterministic stimuli.** Stimulus images are generated from a fixed seed; the set is
  reproducible bit-for-bit. The generator and the manifest (ground-truth counts) are
  included.
- **Fresh, independent calls.** Each repetition is an independent API call (no shared
  conversation/memory), so response variation reflects the model, not context carryover.
- **Keys never committed.** The harness reads API keys from environment variables only.
- **No scripted arithmetic on results.** Means, spreads, and rates in the writeups are
  derived by reading, consistent with the rule above.
