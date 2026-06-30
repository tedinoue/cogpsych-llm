#!/usr/bin/env python3
"""
run_segmented_experiment.py — multi-turn segmented-count INTERFERENCE harness.

Collect-only (raw responses only; no parsing/scoring — see ../PROTOCOL.md). Presents a total
split across N sub-images, one per turn, with an interleaved task between images, and asks
for the total at the end.

THE QUESTION: does occupying the VERBAL channel between counts disrupt the running
dot-count, when occupying a NON-VERBAL channel of comparable presence does not?

ARMS (--arm), all at one fixed cell (total=24, 4 sub-images):
  control : no interleaved turn (the no-interference baseline).
  v-num   : VERBAL, number channel — a 2-digit addition each interleaved turn.
  v-lang  : VERBAL, language channel (non-numeric) — continue a sentence.
  v-desc  : VERBAL, about-the-count (EXPLORATORY; forces re-attention) — describe
            the just-counted dots image in one sentence, without stating a number.
  nv      : NON-VERBAL visual control — same/different on a tiny abstract glyph pair
            (image only, NO per-turn text). Needs --glyphs <dir from gen_glyph_pairs.py>.

PRESENTATION RULE: for the NV arm there is NO per-turn text — all instructions come ONCE in
the opening turn; NV interleaved turns are bare images and the model routes on content. The
verbal arms DO carry per-turn text — that asymmetry IS the manipulation (per-turn text =
the verbal load), not a confound.

MANIPULATION CHECK: we do NOT score the interferer's correctness. We only need EVIDENCE OF
ENGAGEMENT so a null reads as "no interference," not "model skipped it." Every interleaved
reply is logged and tagged so a reader can confirm on-task output per arm.

RAW-ONLY. Writes full transcripts + verbatim final answer to raw.jsonl. No parsing, no
scoring, no extracted-guess column — scoring is done downstream by reading (../PROTOCOL.md).

Retry (429/5xx exp-backoff) + --resume (append, skip completed (arm,total,nseg,variant)).

The API key is read from the environment (GEMINI_API_KEY); it is never passed on the
command line or committed:
  export GEMINI_API_KEY=...   # or use your own secret-injection wrapper
  python3 run_segmented_experiment.py --arm v-num \
    --stimuli stimuli --glyphs glyph_pairs \
    --model gemini-2.5-flash-lite --out data/gemini-2.5-flash-lite/v-num --resume

CACHING NOTE (carried from the control harness): multi-turn re-sends history each turn,
so token cost grows ~quadratically with N_seg. Interleaving DOUBLES the turns, so this
matters MORE here than for the control. Flash-Lite is cheap enough for these runs without
explicit caching; for an expensive model enable cachedContents on the stable prefix first.
"""
import argparse, base64, csv, json, os, random, sys, time, urllib.request, urllib.error

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.5-flash-lite"

# --- Verbal-interferer content pools (fixed + reproducible; drawn per interleaved turn). ---
# v-num: 2-digit additions, sums > 40 and != 24 so the answer can't be confused with the
# dot total (T24) or a plausible per-image count (<=9). No sum equals 24.
ARITHMETIC_POOL = [
    (47, 38), (53, 29), (61, 44), (28, 39), (56, 27),
    (43, 49), (35, 58), (62, 31), (48, 46), (37, 55),
]
# v-lang: neutral, non-numeric sentence stems to continue. No number content.
SENTENCE_STEMS = [
    "The old harbor was quiet except for",
    "By the time the train reached the coast",
    "She opened the cupboard and found",
    "The garden had changed since spring, now",
    "Long after the music stopped",
    "The letter on the table said only that",
    "Where the path forked near the river",
    "Nobody in the village remembered when",
    "The lighthouse keeper wrote that night",
    "Once the storm passed, the fields",
]


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _post(url, payload, max_retries=9):
    """POST with retry on transient errors (429/500/502/503/504). A 503 BURST must NOT
    abort a long run — Flash-Lite throws sustained 503 spells, so use many attempts with a
    capped backoff (cap 60s) totalling several minutes of patience. (Combined with --resume,
    a death is recoverable anyway, but the goal is to not die in the first place.)"""
    data = json.dumps(payload).encode()
    last_err = None
    for attempt in range(max_retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = min(60, 2 ** attempt)   # 1,2,4,8,16,32,60,60,... capped at 60s
                print(f"    [retry] HTTP {e.code}, attempt {attempt+1}/{max_retries}, waiting {wait}s")
                time.sleep(wait); continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < max_retries - 1:
                wait = min(60, 2 ** attempt)
                print(f"    [retry] {type(e).__name__}, attempt {attempt+1}/{max_retries}, waiting {wait}s")
                time.sleep(wait); continue
            raise
    raise last_err


def gemini_multiturn(model, key, turns):
    """turns = ordered list of {"role","text"?,"img_path"?}. Sends the FULL history each
    call (transcript = memory). Returns (reply_text, raw_response_json)."""
    contents = []
    for t in turns:
        parts = []
        if t.get("text"):
            parts.append({"text": t["text"]})
        if t.get("img_path"):
            parts.append({"inline_data": {"mime_type": "image/png", "data": b64(t["img_path"])}})
        contents.append({"role": t["role"], "parts": parts})
    url = f"{GEMINI_BASE}/{model}:generateContent?key={key}"
    resp = _post(url, {"contents": contents})
    try:
        reply = resp["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        reply = None
    return reply, resp


# --- Arm configuration: opening instruction + the interleaved-turn content provider. ---
def opening_instruction(arm, n):
    base = (f"I am going to show you {n} images of dots, one at a time, but I will mix in "
            f"some other items between them. ")
    count_job = ("When I show you an image of dots, count the number of dots in it and tell "
                 "me the count. ")
    final_note = (f"At the very end I will ask you for the total number of dots across all "
                  f"{n} dot-images, so keep track.")
    if arm == "control":
        return (f"I am going to show you {n} images of dots, one at a time. {count_job}{final_note}")
    if arm == "v-num":
        second = ("Between the dot-images I will also give you a short addition problem; when "
                  "I do, just give me the sum. ")
    elif arm == "v-lang":
        second = ("Between the dot-images I will also give you the beginning of a sentence; "
                  "when I do, continue it with one short clause. ")
    elif arm == "v-desc":
        second = ("Between the dot-images I will also ask you to describe the previous dot-image; "
                  "when I do, describe in one sentence what the arrangement of dots looked like, "
                  "without stating a number. ")
    elif arm == "nv":
        # NV: the ONLY place the same/different task is ever described is here, at the start.
        second = ("Between the dot-images I will also show you a small image containing two little "
                  "symbols side by side; when I show you one of those, reply with only one word — "
                  "'same' if the two symbols are identical, or 'different' if they are not. ")
    else:
        raise ValueError(f"unknown arm {arm}")
    return base + count_job + second + final_note


def interference_turn(arm, image_index, glyph_pairs, rng):
    """Return the interleaved-turn dict {"text"?, "img_path"?} for this arm, or None for control.
    Verbal arms -> text (per-turn text IS the verbal load). NV -> a glyph-pair image, NO text."""
    if arm == "control":
        return None
    if arm == "v-num":
        a, b = rng.choice(ARITHMETIC_POOL)
        return {"text": f"What is {a} + {b}?"}
    if arm == "v-lang":
        return {"text": f"Continue this sentence with one short clause: \"{rng.choice(SENTENCE_STEMS)}\""}
    if arm == "v-desc":
        return {"text": "Describe the previous dot-image (the arrangement of the dots) in one "
                        "sentence, without stating a number."}
    if arm == "nv":
        pair = rng.choice(glyph_pairs)
        return {"img_path": pair["pair_path"]}   # NO text — bare image, per the presentation rule
    raise ValueError(f"unknown arm {arm}")


def run_one_session(arm, model, key, seg_paths, total, nseg, variant, glyph_pairs, raw_f):
    """One full interleaved multi-turn session. Logs every turn (tagged by type). Returns the
    verbatim FINAL answer (NOT parsed)."""
    n = len(seg_paths)
    # Per-session RNG so interferer choices are reproducible from (seed-ish) inputs.
    rng = random.Random((total * 1009) ^ (nseg * 97) ^ (variant * 31) ^ hash(arm) & 0xFFFFFFFF)
    history = []
    transcript_log = []

    def step(turn_type, user_text=None, img_path=None):
        history.append({"role": "user", "text": user_text, "img_path": img_path})
        reply, raw = gemini_multiturn(model, key, history)
        history.append({"role": "model", "text": reply or ""})
        transcript_log.append({"turn_type": turn_type, "user": user_text,
                               "img": os.path.basename(img_path) if img_path else None,
                               "model_reply": reply})
        time.sleep(0.5)
        return reply

    # turn 0: the single instruction (states BOTH jobs for interference arms)
    step("instruction", user_text=opening_instruction(arm, n))
    # per-image turns, each followed by an interleaved interference turn (except control)
    for i, p in enumerate(seg_paths):
        step("dots", user_text=f"Image {i+1}:", img_path=p)
        intf = interference_turn(arm, i, glyph_pairs, rng)
        if intf is not None:
            step("interference", user_text=intf.get("text"), img_path=intf.get("img_path"))
    # final: ask for the dot total (prior per-image counts remain in history)
    final = step("final", user_text=(f"Now, what is the total number of dots you counted across "
                                      f"all {n} dot-images? Give the total."))

    rec = {"arm": arm, "model": model, "total_true": total, "nseg": nseg, "variant": variant,
           "n_images": n, "transcript": transcript_log, "final_answer_raw": final}
    raw_f.write(json.dumps(rec) + "\n"); raw_f.flush()
    return final


def load_cells(stimuli_dir):
    """Group segment images by (total, nseg, variant) from the generator manifest, in seg order."""
    man = os.path.join(stimuli_dir, "manifest.csv")
    rows = list(csv.DictReader(open(man)))
    cells = {}
    for r in rows:
        if r["role"] != "segment":
            continue
        key = (int(r["total"]), int(r["nseg"]), int(r["variant"]))
        cells.setdefault(key, []).append((int(r["seg_idx"]), r["path"]))
    return {k: [p for _, p in sorted(v)] for k, v in cells.items()}


def load_glyph_pairs(glyph_dir):
    """Load the glyph-pair manifest (from gen_glyph_pairs.py). Returns list of pair dicts."""
    man = os.path.join(glyph_dir, "manifest.csv")
    return [r for r in csv.DictReader(open(man)) if r["role"] == "glyph_pair"]


def completed_sessions(raw_path):
    """Return the set of (arm,total,nseg,variant) already done (non-null final). For --resume."""
    done = set()
    if os.path.exists(raw_path):
        for line in open(raw_path):
            try:
                r = json.loads(line)
                if r.get("final_answer_raw"):
                    done.add((r.get("arm"), r["total_true"], r["nseg"], r["variant"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["control", "v-num", "v-lang", "v-desc", "nv"])
    ap.add_argument("--stimuli", required=True, help="T24/K4 dots dir from gen_segmented_stimuli.py --grid")
    ap.add_argument("--glyphs", help="glyph-pair dir from gen_glyph_pairs.py (REQUIRED for --arm nv)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0, help="cap sessions this run (0 = all)")
    ap.add_argument("--resume", action="store_true",
                    help="append to existing raw.jsonl + SKIP already-completed sessions")
    ap.add_argument("--out", default="interference_runs")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("GEMINI_API_KEY not set — export it (or use your own secret-injection wrapper) before running.")

    if args.arm == "nv" and not args.glyphs:
        sys.exit("--arm nv requires --glyphs <dir from gen_glyph_pairs.py>")

    cells = load_cells(args.stimuli)
    if not cells:
        sys.exit(f"no segment images found in {args.stimuli}/manifest.csv")
    # Discipline guard: this study is ONE fixed cell (T24/K4). Refuse to silently run a
    # multi-cell stimuli dir (the old set is still on disk) — that would be the scope creep
    # the design forbids. Require the dir to contain ONLY T24/K4.
    bad = sorted({(t, k) for (t, k, _v) in cells.keys()} - {(24, 4)})
    if bad:
        sys.exit(f"stimuli dir has non-(T24/K4) cells {bad} — this study is ONE fixed cell. "
                 f"Regenerate with: gen_segmented_stimuli.py --grid --reps N --seed 2026 --out <dir>")

    glyph_pairs = load_glyph_pairs(args.glyphs) if args.arm == "nv" else []
    if args.arm == "nv" and not glyph_pairs:
        sys.exit(f"no glyph pairs in {args.glyphs}/manifest.csv")

    os.makedirs(args.out, exist_ok=True)
    raw_path = os.path.join(args.out, "raw.jsonl")

    all_sessions = sorted(cells.keys())
    done = completed_sessions(raw_path) if args.resume else set()
    sessions = [s for s in all_sessions if (args.arm, s[0], s[1], s[2]) not in done]
    if args.limit:
        sessions = sessions[: args.limit]

    mode = "a" if args.resume else "w"
    print(f"[run] arm={args.arm}  model={args.model}  to-run={len(sessions)}  "
          f"(already done={len(done)})  out={raw_path}")
    print("[run] RAW-ONLY: full transcripts -> raw.jsonl. AI reads them. No parse/score here.")
    if args.arm != "control":
        print(f"[run] interleaved task per dot-image; manipulation check = engagement visible in raw.")
    with open(raw_path, mode) as raw_f:
        for (total, nseg, variant) in sessions:
            seg_paths = cells[(total, nseg, variant)]
            final = run_one_session(args.arm, args.model, key, seg_paths, total, nseg, variant,
                                    glyph_pairs, raw_f)
            short = (final or "").replace("\n", " ")[:80]
            print(f"  [{args.arm}] T{total}/K{nseg}/v{variant} (true={total}) final: {short!r}")
    print(f"\n[run] done -> {raw_path}")
    print("[run] NEXT: AI-read raw.jsonl — per-image counts, the total, and (bucket 3) whether the")
    print("[run]       total != sum of the model's OWN per-image counts. Compare vs the control arm.")


if __name__ == "__main__":
    main()
