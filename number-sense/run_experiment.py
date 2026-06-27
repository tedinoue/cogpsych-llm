#!/usr/bin/env python3
"""
run_experiment.py — COLLECT-ONLY harness for the number-sense study (cogpsych-llm).

Sends each dot-array PNG to a vision model and logs the model's FULL verbatim response to
raw.jsonl. It does NOT score or analyze responses — see ../PROTOCOL.md. (A rough regex
`guess` column is written to results.csv as a progress indicator only; do not trust it.
Scoring is done by reading raw.jsonl.)

Providers (OpenAI-compatible chat APIs, --provider):
  xai         https://api.x.ai/v1            (Grok)
  openrouter  https://openrouter.ai/api/v1   (Llama, Gemini, Qwen, ... via --model)

KEY HANDLING: never hardcodes a key. Reads it from an environment variable
(XAI_API_KEY or OPENROUTER_API_KEY). Set it however you like, e.g.:
  OPENROUTER_API_KEY=sk-... python3 run_experiment.py --provider openrouter \
      --model google/gemini-2.5-flash-lite --objects-only --stim stimuli --out data/gemini

Main mode for the number-sense study: --objects-only
  single neutral prompt "How many objects are in this image?", `--reps` fresh calls/image.
The repo also retains the original multi-framing / count-noun modes used in the pilot
(A_integer vs open; the dots/shapes/objects/items lexical comparison) for completeness.
"""
import argparse, base64, csv, glob, json, os, re, sys, time, urllib.error, urllib.request

# Provider table: chat endpoint, models endpoint, auth env var, default vision model.
# Both are OpenAI-compatible (same image_url message schema), so one harness serves both.
PROVIDERS = {
    "xai": {
        "chat": "https://api.x.ai/v1/chat/completions",
        "models": "https://api.x.ai/v1/models",
        "env": "XAI_API_KEY",
        "default_model": "grok-4.20-0309-non-reasoning",
    },
    "openrouter": {
        "chat": "https://openrouter.ai/api/v1/chat/completions",
        "models": "https://openrouter.ai/api/v1/models",
        "env": "OPENROUTER_API_KEY",
        "default_model": "google/gemini-2.5-flash-lite",
    },
}
DEFAULT_MODEL = "grok-4.3"  # overridden per --provider/--model

FRAMINGS = {
    "A_integer": "How many dots are in this image? Reply with ONLY a single integer and nothing else.",
    "B_open":    "How many dots are in this image?",
}
PROBE_FRAMINGS = {
    "probe_howmany": "How many dots are in this image?",
    "probe_count":   "Count the dots in this image and tell me the total.",
    "probe_estimate":"Estimate how many dots are in this image. Don't count them one by one — just give your immediate impression as a number.",
}
# NOUN test: hold the image fixed, vary ONLY the count-noun. Tests whether the Type-C
# under-count is LEXICAL ("dots" read as circles, non-circles excluded) or PERCEPTUAL
# (shapes genuinely harder to individuate). If neutral nouns RECOVER accuracy on Type C,
# the deficit is lexical. Each phrased two ways (forced-int + open) folded in below.
NOUN_FRAMINGS = {
    "noun_dots":    "How many dots are in this image?",
    "noun_shapes":  "How many shapes are in this image?",
    "noun_objects": "How many objects are in this image?",
    "noun_items":   "How many separate items are in this image?",
}


def _key(prov):
    k = os.environ.get(prov["env"], "").strip()
    if not k:
        sys.exit(f"{prov['env']} not set. Provide it via the environment, e.g.:\n"
                 f"  {prov['env']}=<your-key> python3 run_experiment.py "
                 f"--provider {('xai' if prov['env']=='XAI_API_KEY' else 'openrouter')} ...")
    return k


def _post(url, payload, key, timeout=120):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get(url, key, timeout=30):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def pick_vision_model(prov, key, prefer):
    """Confirm the requested model id exists on the provider; otherwise just use it as given.
    For OpenRouter the catalog is huge, so we trust an explicit --model and don't auto-pick."""
    try:
        data = _get(prov["models"], key)
        ids = [m.get("id", "") for m in data.get("data", [])]
        if prefer in ids or prov["env"] == "OPENROUTER_API_KEY":
            return prefer, (ids if prefer in ids else [])
        # xAI: vision is unified in grok-4.x; fall back to first grok if exact id absent
        groks = [i for i in ids if "grok" in i and "image" not in i]
        return (groks[0] if groks else prefer), ids
    except Exception as e:
        print(f"[warn] could not list models ({e}); using {prefer}")
        return prefer, []


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def parse_int(text):
    """Extract the model's final number. Uses the LAST standalone integer in the text:
    correct for hidden-reasoning models (only the answer is in content) AND for
    visible-reasoning models (the final answer comes after the reasoning). None if absent."""
    if text is None:
        return None
    nums = re.findall(r"-?\d+", text.replace(",", ""))
    return int(nums[-1]) if nums else None


def ask(chat_url, model, key, img_b64, prompt, max_tokens):
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 1.0,  # fresh variance across reps — we WANT to see response spread
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
    }
    t0 = time.time()
    resp = _post(chat_url, payload, key)
    dt = round(time.time() - t0, 2)
    text = resp["choices"][0]["message"]["content"]
    return text, dt, resp.get("usage", {})


def load_manifest(stim_dir):
    rows = {}
    with open(os.path.join(stim_dir, "manifest.csv")) as f:
        for r in csv.DictReader(f):
            meta = {"n": int(r["n"]), "variant": int(r["variant"]),
                    "total_area_px": float(r["total_area_px"]),
                    "stype": r.get("stype", "A")}
            # normalize to basename in stim_dir so the harness can find the file
            rows[os.path.join(stim_dir, os.path.basename(r["path"]))] = meta
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="xai", choices=list(PROVIDERS),
                    help="xai (Grok direct) or openrouter (Qwen/Llama/etc.)")
    ap.add_argument("--stim", default="stimuli")
    ap.add_argument("--out", default="runs/pilot")
    ap.add_argument("--reps", type=int, default=3, help="fresh calls per image x framing")
    ap.add_argument("--model", default=None, help="model id; default = provider's default")
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--probe-n", type=int, default=12, help="set size for the framing probe")
    ap.add_argument("--sleep", type=float, default=0.4, help="pause between calls (politeness)")
    ap.add_argument("--noun-test", default=None,
                    help="run ONLY the count-noun comparison on this stimulus type (e.g. C). "
                         "Holds image fixed, varies dots/shapes/objects/items.")
    ap.add_argument("--noun-types", default="A,C",
                    help="stimulus types to include in --noun-test (compare shapes vs circles)")
    ap.add_argument("--hint-summary", action="store_true",
                    help="print a ROUGH regex-parsed summary as a sanity hint only. PROTOCOL: this is "
                         "NOT analysis — the AI reads raw.jsonl and does all scoring. Off by default.")
    ap.add_argument("--objects-only", action="store_true",
                    help="single neutral framing 'How many objects are in this image?' across all "
                         "images (no forced-int, no probe, no nouns). The real-run config: collect raw.")
    args = ap.parse_args()

    prov = PROVIDERS[args.provider]
    chat_url = prov["chat"]
    want_model = args.model or prov["default_model"]
    key = _key(prov)
    model, all_ids = pick_vision_model(prov, key, want_model)
    print(f"[provider] {args.provider}   [model] using: {model}")

    manifest = load_manifest(args.stim)
    images = sorted(manifest.keys())
    if not images:
        sys.exit(f"no images found via manifest in {args.stim}")

    os.makedirs(args.out, exist_ok=True)
    raw_path = os.path.join(args.out, "raw.jsonl")
    csv_path = os.path.join(args.out, "results.csv")
    raw_f = open(raw_path, "w")
    rows = []

    def run_one(img, prompt, framing, rep, max_tokens):
        meta = manifest[img]
        try:
            text, dt, usage = ask(chat_url, model, key, b64(img), prompt, max_tokens)
            # NON-AUTHORITATIVE convenience hint only. PROTOCOL: scripts do not parse/score
            # LLM responses — the AI reads `raw` and does all analysis. This regex is a rough
            # progress indicator in the console, NEVER trusted as data. (see PROTOCOL.md)
            guess = parse_int(text)
            err = None
        except Exception as e:
            text, dt, usage, guess, err = None, None, {}, None, str(e)
        rec = {"image": os.path.basename(img), "stype": meta.get("stype", "A"),
               "true_n": meta["n"], "variant": meta["variant"],
               "total_area_px": meta["total_area_px"], "framing": framing, "rep": rep,
               "guess": guess, "raw": text, "latency_s": dt, "error": err}
        raw_f.write(json.dumps(rec) + "\n"); raw_f.flush()
        rows.append(rec)
        tag = f"t{meta.get('stype','A')} n={meta['n']:2d} v{meta['variant']} {framing:14s} rep{rep}"
        print(f"  {tag} -> {guess}" + (f"   [ERR {err}]" if err else ""))
        time.sleep(args.sleep)

    # --- NOUN TEST MODE: only the count-noun comparison, then summarize + return ---
    if args.noun_test is not None:
        want_types = [t.strip() for t in args.noun_types.split(",") if t.strip()]
        sel = [i for i in images if manifest[i].get("stype", "A") in want_types]
        print(f"\n=== NOUN test on types {want_types}: {len(sel)} images "
              f"x {len(NOUN_FRAMINGS)} nouns x {args.reps} reps ===")
        for img in sel:
            for framing, prompt in NOUN_FRAMINGS.items():
                for rep in range(args.reps):
                    run_one(img, prompt, framing, rep, args.max_tokens)
        raw_f.close()
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["image", "stype", "true_n", "variant",
                                              "total_area_px", "framing", "rep", "guess",
                                              "latency_s", "error"])
            w.writeheader()
            for r in rows:
                w.writerow({k: r[k] for k in w.fieldnames})
        print(f"\nWrote {len(rows)} calls -> {csv_path}  (raw: {raw_path})")
        print("PROTOCOL: collect-only. Read raw.jsonl and score by reading (see PROTOCOL.md).")
        if args.hint_summary:
            summarize_noun(rows, want_types)
        return

    # --- OBJECTS-ONLY MODE: single neutral framing, collect raw, then return ---
    if args.objects_only:
        prompt = "How many objects are in this image?"
        print(f"\n=== OBJECTS-ONLY: {len(images)} images x {args.reps} reps "
              f"(neutral wording, collect-only) ===")
        for img in images:
            for rep in range(args.reps):
                run_one(img, prompt, "objects", rep, args.max_tokens)
        raw_f.close()
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["image", "stype", "true_n", "variant",
                                              "total_area_px", "framing", "rep", "guess",
                                              "latency_s", "error"])
            w.writeheader()
            for r in rows:
                w.writerow({k: r[k] for k in w.fieldnames})
        print(f"\nWrote {len(rows)} calls -> {csv_path}  (raw: {raw_path})")
        print("PROTOCOL: collect-only. Read raw.jsonl and score by reading (see PROTOCOL.md).")
        return

    # Forced-integer normally needs few tokens, BUT a visible-reasoning model ("thinking")
    # emits its serial count in the content before the answer and truncates if capped low.
    is_thinking = "thinking" in model.lower()
    forced_cap = args.max_tokens if is_thinking else 20

    # Main A/B sweep across all images
    print(f"\n=== A/B sweep: {len(images)} images x {len(FRAMINGS)} framings x {args.reps} reps "
          f"(forced-int cap={forced_cap}{', thinking model' if is_thinking else ''}) ===")
    for img in images:
        for framing, prompt in FRAMINGS.items():
            mt = forced_cap if framing == "A_integer" else args.max_tokens
            for rep in range(args.reps):
                run_one(img, prompt, framing, rep, mt)

    # Framing probe on one mid-size image (3 framings)
    probe_imgs = [i for i in images if manifest[i]["n"] == args.probe_n
                  and manifest[i].get("stype", "A") == "A"]
    if probe_imgs:
        pim = probe_imgs[0]
        print(f"\n=== framing probe on {os.path.basename(pim)} (n={args.probe_n}) x {args.reps} reps ===")
        for framing, prompt in PROBE_FRAMINGS.items():
            for rep in range(args.reps):
                run_one(pim, prompt, framing, rep, args.max_tokens)

    raw_f.close()
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["image", "stype", "true_n", "variant", "total_area_px",
                                          "framing", "rep", "guess", "latency_s", "error"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    print(f"\nWrote {len(rows)} calls -> {csv_path}  (raw: {raw_path})")
    print("PROTOCOL: collect-only. Read raw.jsonl and score by reading (see PROTOCOL.md).")
    if args.hint_summary:
        summarize(rows)


def summarize_noun(rows, want_types):
    """Did neutral count-nouns recover accuracy that 'dots' lost? Break out by type x noun."""
    order = ["noun_dots", "noun_shapes", "noun_objects", "noun_items"]
    nouns = [n for n in order if any(r["framing"] == n for r in rows)]
    print("\n" + "=" * 64)
    print("NOUN TEST SUMMARY  (does neutral wording recover Type-C accuracy?)")
    print("=" * 64)
    for t in want_types:
        tr = [r for r in rows if r.get("stype", "A") == t and r["guess"] is not None]
        if not tr:
            continue
        print(f"\n[type {t}]  exact% / mean-signed-err, pooled over all set sizes & variants:")
        print("   noun        | exact% | mean-err | mean|err| | n_calls")
        for nn in nouns:
            g = [(r["guess"], r["true_n"]) for r in tr if r["framing"] == nn]
            if not g:
                continue
            exact = 100 * sum(1 for (x, n) in g if x == n) / len(g)
            merr = sum(x - n for (x, n) in g) / len(g)
            mabs = sum(abs(x - n) for (x, n) in g) / len(g)
            print(f"   {nn:11s} | {exact:5.0f}% | {merr:+8.2f} | {mabs:8.2f} | {len(g)}")
    # the money line: Type-C dots-vs-neutral gap (if C present)
    if "C" in want_types:
        cr = [r for r in rows if r.get("stype") == "C" and r["guess"] is not None]
        def cabs(nn):
            g = [(r["guess"], r["true_n"]) for r in cr if r["framing"] == nn]
            return (sum(abs(x - n) for (x, n) in g) / len(g)) if g else None
        d = cabs("noun_dots")
        neutral = [cabs(n) for n in ("noun_shapes", "noun_objects", "noun_items") if cabs(n) is not None]
        if d is not None and neutral:
            best = min(neutral)
            print(f"\n[VERDICT] Type-C mean|err|: 'dots'={d:.2f}  vs  best-neutral={best:.2f}")
            if best < d * 0.6:
                print("  -> neutral wording RECOVERS accuracy -> the deficit is LEXICAL ('dots'=circles),")
                print("     not perceptual. Clean lexical-vs-perceptual dissociation. On-thesis.")
            elif best < d * 0.9:
                print("  -> neutral wording PARTIALLY recovers -> mixed lexical + perceptual deficit.")
            else:
                print("  -> neutral wording does NOT recover -> the Type-C deficit is PERCEPTUAL")
                print("     (heterogeneous shapes genuinely harder to individuate), not just lexical.")
    print("\n  reps are fresh calls; small n per cell — pilot signal, not powered stats.")


def summarize(rows):
    """Eyeball report: accuracy vs N, repetition spread (CV), A-vs-B gap, framing probe."""
    import statistics as st

    def cell(framing):
        by_n = {}
        for r in rows:
            if r["framing"] != framing or r["guess"] is None:
                continue
            by_n.setdefault(r["true_n"], []).append(r["guess"])
        return by_n

    print("\n" + "=" * 64)
    print("EYEBALL SUMMARY")
    print("=" * 64)
    for framing in ("A_integer", "B_open"):
        by_n = cell(framing)
        if not by_n:
            continue
        print(f"\n[{framing}]   true_n | guesses           | mean  | CV    | exact%")
        for n in sorted(by_n):
            g = by_n[n]
            mean = sum(g) / len(g)
            cv = (st.pstdev(g) / mean) if mean else 0.0
            exact = 100 * sum(1 for x in g if x == n) / len(g)
            gs = ",".join(str(x) for x in g)
            print(f"            {n:6d} | {gs:17s} | {mean:5.1f} | {cv:5.3f} | {exact:4.0f}%")

    # A-vs-B gap (the analog-vs-counting knob): per-N exact-match rate difference
    a, b = cell("A_integer"), cell("B_open")
    common = sorted(set(a) & set(b))
    if common:
        print("\n[A vs B]  exact% by framing (A=forced-int, B=open):")
        print("   true_n |  A_exact% | B_exact%")
        for n in common:
            ae = 100 * sum(1 for x in a[n] if x == n) / len(a[n])
            be = 100 * sum(1 for x in b[n] if x == n) / len(b[n])
            print(f"   {n:6d} | {ae:7.0f}% | {be:7.0f}%")

    # BY STIMULUS TYPE — the area/shape-confound comparison.
    # A = uniform circles, B = extreme size variation, C = mixed shapes.
    # Pool the A/B framings (exclude the probe_* rows) and split by type.
    types = sorted({r.get("stype", "A") for r in rows if not r["framing"].startswith("probe_")})
    if len(types) > 1:
        print("\n[BY STIMULUS TYPE]  (A=uniform circles, B=extreme size var, C=mixed shapes)")
        print("   pooled over A_integer + B_open framings; signed error = guess - true_n")
        # collect per (type, n)
        cellt = {}
        for r in rows:
            if r["framing"].startswith("probe_") or r["guess"] is None:
                continue
            cellt.setdefault((r.get("stype", "A"), r["true_n"]), []).append(r["guess"])
        all_n = sorted({n for (_, n) in cellt})
        header = "   true_n | " + " | ".join(f"{t}: exact% / mean-err" for t in types)
        print(header)
        for n in all_n:
            parts = []
            for t in types:
                g = cellt.get((t, n), [])
                if not g:
                    parts.append("   --   /  -- ")
                    continue
                exact = 100 * sum(1 for x in g if x == n) / len(g)
                merr = sum(x - n for x in g) / len(g)
                parts.append(f"{exact:4.0f}% / {merr:+5.1f}")
            print(f"   {n:6d} | " + " | ".join(parts))
        # one-line per-type aggregate above the subitizing range (n>=4), where the confound bites
        print("\n   aggregate for n>=4 (where area/shape could substitute for number):")
        for t in types:
            g = [(x, n) for (tt, n), gg in cellt.items() if tt == t and n >= 4 for x in gg]
            if not g:
                continue
            exact = 100 * sum(1 for (x, n) in g if x == n) / len(g)
            mabs = sum(abs(x - n) for (x, n) in g) / len(g)
            mbias = sum((x - n) for (x, n) in g) / len(g)
            print(f"     type {t}:  exact={exact:4.0f}%   mean|err|={mabs:4.2f}   bias={mbias:+5.2f}")
        print("   -> if B (size var) and C (shapes) match A, the model tracks NUMBER, not area/blob shape.")
        print("   -> if B/C degrade vs A, accuracy was riding on area/uniform-circle cues (confound real).")

    # Framing probe
    probe = {}
    for r in rows:
        if r["framing"].startswith("probe_") and r["guess"] is not None:
            probe.setdefault(r["framing"], []).append(r["guess"])
    if probe:
        print("\n[framing probe] (single mid-size image):")
        for fr, g in probe.items():
            mean = sum(g) / len(g)
            print(f"   {fr:16s} guesses={g}  mean={mean:.1f}")

    print("\nReads:")
    print("  * CV roughly CONSTANT across N (and >0)            -> Weberian/analog signature (human-like)")
    print("  * CV ~0 with exact%=100 up to high N               -> deterministic counting (non-biological)")
    print("  * exact% high small-N then cliff                   -> subitizing-like regime boundary")
    print("  * A (forced) << B (open) in exact%                 -> open framing lets it serially count (CoT knob)")
    print("  * 'estimate-don't-count' probe lower/biased        -> framing selects between regimes (claim 3 has legs)")


if __name__ == "__main__":
    main()
