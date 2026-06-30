#!/usr/bin/env python3
"""
gen_glyph_pairs.py — tiny abstract-glyph same/different pairs for the NON-VERBAL
interference arm (Arm NV) of the segmented-counting interference experiment.

WHY THIS EXISTS:
  The NV arm needs an interleaved task that occupies a NON-VERBAL channel of
  comparable presence to the verbal arms, with NO per-turn text and NO semantic/
  linguistic content. Real emoji were REJECTED for the control: prior work on emoji as identity tokens (#238) shows an emoji activates a rich semantic/linguistic
  constellation, so a pictured emoji might route to the SAME concept space a
  codepoint would and smuggle language through the visual door — contaminating
  the very channel the NV arm is meant to keep clean (and invisibly: "same"
  looks identical whether judged on shape or on meaning). Fix: SEMANTICALLY-EMPTY
  abstract glyphs — procedurally-generated small non-iconic symbols with no word/
  concept to route to, so a same/different judgment MUST be made on visual form.

  TOKEN ECONOMY : glyphs are TINY on purpose. A few image tokens each, so the
  NV interleaved stimulus is comparable in input mass to the dots images and does
  NOT differ from the verbal arms in token weight (that itself would be a confound).

NO EXTRACTOR. Renders images + a ground-truth manifest only. Does not call a model,
parse, score, or guess. (Same collect-only hygiene as the dot generator.)

DETERMINISTIC: everything derives from a single integer seed; the set regenerates
byte-identically. Same seed discipline as gen_segmented_stimuli.py.

A "pair" = two small glyph images shown together on the interleaved turn. The model
is told ONCE at the start (by the harness) to reply only same/different. The pair is
SAME (identical glyph) or DIFFERENT (one glyph element changed). Ground truth recorded.

Usage:
  python3 gen_glyph_pairs.py --n 60 --seed 2026 --out glyph_pairs
  # produces n pairs (balanced same/different), each pair = 2 PNGs + a composite,
  # plus manifest.csv with the same/different ground truth.
Each rendered file:
  glyph_v{variant}_a_s{seed}.png   (left glyph)
  glyph_v{variant}_b_s{seed}.png   (right glyph)
  glyph_v{variant}_pair_s{seed}.png (the two side by side, the actual stimulus sent)
"""
import argparse, csv, math, os, random, sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("PIL/Pillow not available — install Pillow or run where PIL exists.")

# --- Tiny canvas (cost lever / token economy). One glyph per small square. ---
GLYPH_CANVAS = 64          # per-glyph square (px). Tiny on purpose; verify glyphs read.
PAIR_GAP = 2               # gap between the two glyphs in the composite (2px)
BORDER = 2                 # black border around each glyph (2px) — makes the
                           # two glyphs in a pair unambiguously separate boxes, not one blob.
MARGIN = 8
BG = (255, 255, 255)
INK = (20, 20, 20)

# A glyph is a small set of abstract strokes placed on a coarse grid inside the
# canvas. No icon, no letter, no digit — just line/arc/dot primitives. The grid
# keeps them well-defined and resolvable; randomness over primitives + grid cells
# makes each variant distinct without any of them meaning anything.
PRIMITIVES = ("line", "arc", "dot", "vbar", "hbar", "diag")
N_STROKES = 3              # strokes per glyph — enough to be distinctive, few enough to read at 64px


def _grid_points(canvas, n=3):
    """Return the centers of an n x n grid of cells inside the margins."""
    lo, hi = MARGIN, canvas - MARGIN
    step = (hi - lo) / (n - 1) if n > 1 else 0
    return [(int(lo + c * step), int(lo + r * step)) for r in range(n) for c in range(n)]


def _draw_primitive(d, kind, cx, cy, size, rng):
    """Draw one abstract stroke of the given kind centered near (cx, cy)."""
    s = size
    if kind == "line":
        d.line([cx - s, cy - s, cx + s, cy + s], fill=INK, width=3)
    elif kind == "diag":
        d.line([cx - s, cy + s, cx + s, cy - s], fill=INK, width=3)
    elif kind == "vbar":
        d.line([cx, cy - s, cx, cy + s], fill=INK, width=3)
    elif kind == "hbar":
        d.line([cx - s, cy, cx + s, cy], fill=INK, width=3)
    elif kind == "arc":
        start = rng.choice((0, 90, 180, 270))
        d.arc([cx - s, cy - s, cx + s, cy + s], start, start + 180, fill=INK, width=3)
    elif kind == "dot":
        r = max(2, s // 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK)


def _glyph_spec(rng):
    """A glyph = a list of (primitive, grid_cell_index). Abstract, meaningless."""
    cells = list(range(9))
    rng.shuffle(cells)
    chosen_cells = cells[:N_STROKES]
    return [(rng.choice(PRIMITIVES), c) for c in chosen_cells]


def _render_glyph(spec, path):
    img = Image.new("RGB", (GLYPH_CANVAS, GLYPH_CANVAS), BG)
    d = ImageDraw.Draw(img)
    pts = _grid_points(GLYPH_CANVAS, 3)
    size = GLYPH_CANVAS // 6
    for kind, cell in spec:
        cx, cy = pts[cell]
        _draw_primitive(d, kind, cx, cy, size, rng=random.Random(cell * 7 + len(kind)))
    # 2px black border around the glyph  — unambiguous box edge.
    for b in range(BORDER):
        d.rectangle([b, b, GLYPH_CANVAS - 1 - b, GLYPH_CANVAS - 1 - b], outline=INK)
    img.save(path)


def _mutate(spec, rng):
    """Produce a clearly-DIFFERENT glyph (make 'different' pairs more
    distinct — change MULTIPLE strokes, not one, so the discrimination is unambiguous).
    Changes ~2/3 of the strokes (primitive and/or cell), guaranteeing at least 2 changes."""
    spec = [list(s) for s in spec]
    n = len(spec)
    n_change = max(2, (2 * n) // 3)                 # at least 2 strokes change
    idxs = list(range(n)); rng.shuffle(idxs)
    for i in idxs[:n_change]:
        if rng.random() < 0.5:
            spec[i][0] = rng.choice([p for p in PRIMITIVES if p != spec[i][0]])
        else:
            used = {c for _, c in spec}
            free = [c for c in range(9) if c not in used]
            if free:
                spec[i][1] = rng.choice(free)
            else:
                spec[i][0] = rng.choice([p for p in PRIMITIVES if p != spec[i][0]])
    out = [tuple(s) for s in spec]
    return out


def _composite(path_a, path_b, out_path):
    """Two glyphs side by side on one image = the stimulus actually sent on the turn."""
    a = Image.open(path_a); b = Image.open(path_b)
    w = a.width + PAIR_GAP + b.width
    h = max(a.height, b.height)
    canvas = Image.new("RGB", (w, h), BG)
    canvas.paste(a, (0, 0)); canvas.paste(b, (a.width + PAIR_GAP, 0))
    canvas.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="number of pairs (balanced same/different)")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="glyph_pairs")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    rng = random.Random(args.seed ^ 0x6C7970)  # "glyp"
    rows = []
    for v in range(args.n):
        is_same = (v % 2 == 0)   # balanced: even variants same, odd different
        spec_a = _glyph_spec(rng)
        a_path = os.path.join(args.out, f"glyph_v{v}_a_s{args.seed}.png")
        b_path = os.path.join(args.out, f"glyph_v{v}_b_s{args.seed}.png")
        pair_path = os.path.join(args.out, f"glyph_v{v}_pair_s{args.seed}.png")
        _render_glyph(spec_a, a_path)
        if is_same:
            _render_glyph(spec_a, b_path)        # identical glyph
        else:
            spec_b = _mutate(spec_a, rng)
            _render_glyph(spec_b, b_path)
        _composite(a_path, b_path, pair_path)
        rows.append({"role": "glyph_pair", "variant": v,
                     "ground_truth": "same" if is_same else "different",
                     "seed": args.seed, "canvas": GLYPH_CANVAS,
                     "path_a": a_path, "path_b": b_path, "pair_path": pair_path})

    man = os.path.join(args.out, "manifest.csv")
    with open(man, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["role", "variant", "ground_truth", "seed",
                                          "canvas", "path_a", "path_b", "pair_path"])
        w.writeheader(); w.writerows(rows)

    n_same = sum(1 for r in rows if r["ground_truth"] == "same")
    print(f"Wrote {len(rows)} glyph pairs ({n_same} same / {len(rows)-n_same} different) "
          f"-> {args.out}/  (manifest: {man})")
    print("These are ABSTRACT, semantically-empty (no emoji/letter/digit) — the NON-VERBAL")
    print("interference stimulus. The harness sends the *_pair_s*.png composite per interleaved turn.")
    print("NEXT: eyeball a few — confirm glyphs are individually resolvable + the one-element")
    print("      'different' change is visible at 64px BEFORE a full run. AI-read only, no parse.")


if __name__ == "__main__":
    main()
