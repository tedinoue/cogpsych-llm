#!/usr/bin/env python3
"""
gen_dots.py — deterministic dot-array stimulus generator for the LLM number-cognition
("LLM Piraha") pilot. Companion to inverted-genesis_EXPERIMENT_number-cognition.md.

Design notes (pilot scope):
  - EXACT N: we draw exactly N non-overlapping filled circles. No generative model
    (a generative image cannot guarantee exactly-N — that confound kills the study).
  - SIZE JITTER (crude area de-correlation, pilot version): individual dot radius is
    randomized within a band each trial, so total-dot-area does NOT monotonically track
    N across the set. This is the pilot's cheap guard against "the model is reading blob
    area, not number." The REAL run upgrades this to a full size x number factorial where
    on some trials more-numerous = LESS-total-area (Halberda/Dehaene standard).
  - REPRODUCIBLE: everything derives from a single integer seed, so the exact image set
    can be regenerated and the analysis is auditable.

Usage:
  python3 gen_dots.py                       # default set, writes ./stimuli/
  python3 gen_dots.py --sizes 2,4,7,12,18 --reps 1 --seed 42 --out stimuli
Each output PNG is named  dot_n{N}_v{variant}_s{seed}.png  and a manifest.csv records
the ground truth (n, variant, seed, total_area_px, mean_radius, path).
"""
import argparse, csv, math, os, random, sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("PIL/Pillow not available — install Pillow or run where PIL exists.")

CANVAS = 1024         # square canvas (px); enlarged so high-N (up to 40) packs without crowding
MARGIN = 40           # keep dots off the edge
BG = (255, 255, 255)  # white background
DOT = (20, 20, 20)    # near-black items (high contrast, color is a nuisance var for the real run)
# size bands are per stimulus-type (see TYPES below), not global


def _place_dots(n, rng, rmin, rmax, max_tries=40000):
    """Return list of (cx, cy, r) non-overlapping using radius band [rmin,rmax], or raise."""
    dots = []
    tries = 0
    while len(dots) < n:
        tries += 1
        if tries > max_tries:
            raise RuntimeError(f"could not pack {n} items in {CANVAS}px canvas "
                               f"(placed {len(dots)}). Lower N, enlarge canvas, or shrink size band.")
        r = rng.randint(rmin, rmax)
        cx = rng.randint(MARGIN + r, CANVAS - MARGIN - r)
        cy = rng.randint(MARGIN + r, CANVAS - MARGIN - r)
        ok = True
        for (ox, oy, orr) in dots:
            # treat r as a bounding radius; keep a small gap so items read as separate
            if (cx - ox) ** 2 + (cy - oy) ** 2 < (r + orr + 6) ** 2:
                ok = False
                break
        if ok:
            dots.append((cx, cy, r))
    return dots


# Stimulus types. "sides": 0 => circle; >=3 => regular polygon with that many sides.
# Type A = uniform-ish circles (original). B = extreme size variation, circles only.
# C = mixed shapes (rect..hexagon..circle), moderate size variation.
TYPES = {
    "A": {"rmin": 8,  "rmax": 34, "shapes": [0]},                 # circles, moderate jitter (original)
    "B": {"rmin": 5,  "rmax": 70, "shapes": [0]},                 # circles, EXTREME size variation
    "C": {"rmin": 10, "rmax": 40, "shapes": [0, 3, 4, 5, 6]},     # circle/triangle/square/pentagon/hexagon
}


def _poly_points(cx, cy, r, sides, rot):
    pts = []
    for k in range(sides):
        a = rot + 2 * math.pi * k / sides
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _shape_area(r, sides):
    if sides == 0:
        return math.pi * r * r
    # area of regular polygon inscribed in circle radius r
    return 0.5 * sides * r * r * math.sin(2 * math.pi / sides)


def render(n, variant, seed, out_dir, stype):
    cfg = TYPES[stype]
    # per-image seed folds in n + variant + type so each image is independent yet reproducible
    type_salt = sum(ord(c) for c in stype)
    rng = random.Random((seed * 1000003) ^ (n * 131) ^ (variant * 17) ^ (type_salt * 7919))
    # Adaptive size band for high N: keep size-jitter (area-decorrelation) but shrink the band
    # so N up to 40 packs non-overlapping on the canvas. Below N=15 use the type's native band.
    rmin, rmax = cfg["rmin"], cfg["rmax"]
    if n > 15:
        scale = max(0.45, (15.0 / n) ** 0.5)  # gentle shrink, floored so dots stay visible
        rmin = max(5, int(rmin * scale))
        rmax = max(rmin + 4, int(rmax * scale))
    items = _place_dots(n, rng, rmin, rmax)
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    d = ImageDraw.Draw(img)
    total_area = 0.0
    shapes_used = []
    for (cx, cy, r) in items:
        sides = rng.choice(cfg["shapes"])
        if sides == 0:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOT)
        else:
            rot = rng.uniform(0, 2 * math.pi)
            d.polygon(_poly_points(cx, cy, r, sides, rot), fill=DOT)
        total_area += _shape_area(r, sides)
        shapes_used.append(sides)
    fname = f"dot_t{stype}_n{n:02d}_v{variant}_s{seed}.png"
    path = os.path.join(out_dir, fname)
    img.save(path)
    mean_r = sum(r for (_, _, r) in items) / len(items)
    return {"stype": stype, "n": n, "variant": variant, "seed": seed,
            "total_area_px": round(total_area, 1), "mean_radius": round(mean_r, 2),
            "n_circles": shapes_used.count(0), "path": path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="1,2,3,4,5,7,9,12,15,18",
                    help="comma-separated set sizes (default spans subitizing->cliff->high-N)")
    ap.add_argument("--reps", type=int, default=2,
                    help="distinct image variants per set size (different layouts)")
    ap.add_argument("--types", default="A,B,C",
                    help="stimulus types: A=uniform circles, B=extreme size variation, C=mixed shapes")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="stimuli")
    args = ap.parse_args()

    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    for t in types:
        if t not in TYPES:
            sys.exit(f"unknown type {t!r}; known: {','.join(TYPES)}")
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for t in types:
        for n in sizes:
            for v in range(args.reps):
                rows.append(render(n, v, args.seed, args.out, t))

    man = os.path.join(args.out, "manifest.csv")
    with open(man, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stype", "n", "variant", "seed", "total_area_px",
                                          "mean_radius", "n_circles", "path"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} images to {args.out}/  (manifest: {man})")
    # sanity report per type: confirm area does NOT cleanly track N (the de-correlation we want)
    for t in types:
        print(f"\n[type {t}]  n | mean_total_area_px")
        by_n = {}
        for r in rows:
            if r["stype"] == t:
                by_n.setdefault(r["n"], []).append(r["total_area_px"])
        prev = None
        flagged = True
        for n in sizes:
            a = by_n[n]
            m = sum(a) / len(a)
            mark = ""
            if prev is not None and m < prev:
                mark = "  <- area DROPS as N rises (good de-correlation)"
                flagged = False
            print(f"        {n:2d} | {m:10.0f}{mark}")
            prev = m
        if flagged:
            print("        (!) area rose monotonically with N — widen this type's size band")


if __name__ == "__main__":
    main()
