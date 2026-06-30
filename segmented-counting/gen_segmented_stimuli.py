#!/usr/bin/env python3
"""
gen_segmented_stimuli.py — segmented sequential dot-count stimulus generator.

Companion to PROTOCOL.md.
Generates, for a target TOTAL split into N_SEG segments, a set of N_SEG small images
each holding a known exact count, whose counts sum to TOTAL. Plus a MARGINED-SINGLE
image (Stage 0a): the same dots composited into one image, for the baseline.

WHY A SEPARATE GENERATOR (not a flag on gen_dots.py):
  - seam-by-construction: a dot can never straddle a segment boundary because each
    segment is rendered as its own image with its own internal margin. There is no
    "cutting" of a finished image, so no straddle artifact (the failure class that
    would masquerade as a model limit).
  - small canvas by default (cost lever): image *tokens* scale with pixel
    dimensions and dominate billing. Default canvas is small; VERIFY dots stay
    individually resolvable at the chosen size (a too-small canvas that merges
    adjacent dots manufactures undercounting — same artifact class as the seam).
  - the original gen_dots.py is left untouched as the historical tool behind
    committed single-image results.

NO EXTRACTOR. This script only RENDERS images + writes a ground-truth manifest.
It does NOT call any model, parse, score, or guess. (The collection harness is a
separate, also-extractor-free script; per protocol, scoring is a downstream AI-read
artifact. Do NOT add a parse/guess path here or there.)

DETERMINISTIC: everything derives from a single integer seed; the exact set regenerates.

Usage:
  python3 gen_segmented_stimuli.py --total 24 --nseg 3 --reps 20 --seed 42 --out seg_stimuli
  python3 gen_segmented_stimuli.py --grid                # emit the fixed cell
Each rendered file:  seg_T{total}_K{nseg}_v{variant}_p{segidx}_s{seed}.png   (a segment)
                     seg_T{total}_K{nseg}_v{variant}_single_s{seed}.png       (margined single, Stage 0a)
manifest.csv records ground truth at BOTH levels: per-segment count and total.
"""
import argparse, csv, math, os, random, sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("PIL/Pillow not available — install Pillow or run where PIL exists.")

# --- Small canvas by default (cost lever). VERIFY resolvability before a full run. ---
SEG_CANVAS = 256        # per-segment square (px). Small on purpose. Sweep candidates: 192/256/320.
SINGLE_CANVAS = 384     # margined-single composite is a bit larger (holds all dots)
MARGIN = 14             # internal keep-off-edge; also the de-facto seam margin (each seg is its own image)
BG = (255, 255, 255)
DOT = (20, 20, 20)
RMIN, RMAX = 6, 16      # dot radius band, small-canvas-appropriate; jittered for area de-correlation
GAP = 5                 # min gap between dots so they read as separate at small size


MAX_PER_SEG = 9   # cap per-segment count so per-image counting sits in the
                  # near-exact regime for thinking models. Set to 9 because prior data shows
                  # reasoning models count EXACT with ZERO VARIANCE up to 9 (not 7 — 9 is the
                  # measured ceiling of the safe regime; gives more per-segment flexibility +
                  # fewer segments per total). This isolates the CARRY from per-image counting —
                  # a total error is then attributable to carrying, not to failing to count a
                  # crowded sub-image. Also keeps per-segment counts below the high-N regime where
                  # round-number ATTRACTORS fire, so attractor risk lives only at the total level.


def _split_total(total, nseg, rng):
    """Partition `total` into nseg per-segment counts, each in [1, MAX_PER_SEG].
    NOT forced even (forced divisibility is its own confound — a model could exploit
    equal-per-segment structure); balanced-ish but jittered. Requires nseg*MAX_PER_SEG >= total
    (caller must pick nseg large enough for the total given the cap)."""
    if total > nseg * MAX_PER_SEG:
        raise ValueError(f"total {total} needs > {nseg} segments at cap {MAX_PER_SEG}/seg "
                         f"(max holdable = {nseg*MAX_PER_SEG}). Raise nseg or lower total.")
    if nseg == 1:
        if total > MAX_PER_SEG:
            raise ValueError(f"nseg=1 with total {total} exceeds per-seg cap {MAX_PER_SEG}")
        return [total]
    base = total // nseg
    parts = [base] * nseg
    rem = total - base * nseg
    for i in range(rem):
        parts[i % nseg] += 1
    # jitter without violating the cap or dropping below 1
    for _ in range(nseg * 2):
        i, j = rng.randrange(nseg), rng.randrange(nseg)
        if parts[i] > 1 and parts[j] < MAX_PER_SEG:
            parts[i] -= 1
            parts[j] += 1
    rng.shuffle(parts)
    assert sum(parts) == total and all(1 <= p <= MAX_PER_SEG for p in parts)
    return parts


def _place(n, canvas, rng, max_tries=20000):
    dots = []
    tries = 0
    while len(dots) < n:
        tries += 1
        if tries > max_tries:
            raise RuntimeError(f"could not pack {n} dots in {canvas}px (placed {len(dots)}). "
                               f"Raise canvas, lower per-seg count, or shrink RMIN/RMAX/GAP.")
        r = rng.randint(RMIN, RMAX)
        cx = rng.randint(MARGIN + r, canvas - MARGIN - r)
        cy = rng.randint(MARGIN + r, canvas - MARGIN - r)
        if all((cx - ox) ** 2 + (cy - oy) ** 2 >= (r + orr + GAP) ** 2 for ox, oy, orr in dots):
            dots.append((cx, cy, r))
    return dots


def _draw(dots, canvas, path):
    img = Image.new("RGB", (canvas, canvas), BG)
    d = ImageDraw.Draw(img)
    area = 0.0
    for cx, cy, r in dots:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOT)
        area += math.pi * r * r
    img.save(path)
    return round(area, 1)


def render_set(total, nseg, variant, seed, out_dir):
    """Render one set: nseg segment images + 1 margined-single composite. Returns manifest rows."""
    rng = random.Random((seed * 1000003) ^ (total * 131) ^ (nseg * 911) ^ (variant * 17))
    parts = _split_total(total, nseg, rng)
    rows = []
    for p_idx, pc in enumerate(parts):
        dots = _place(pc, SEG_CANVAS, rng)
        fname = f"seg_T{total:02d}_K{nseg}_v{variant}_p{p_idx}_s{seed}.png"
        path = os.path.join(out_dir, fname)
        area = _draw(dots, SEG_CANVAS, path)
        rows.append({"role": "segment", "total": total, "nseg": nseg, "variant": variant,
                     "seg_idx": p_idx, "seg_count": pc, "seed": seed,
                     "canvas": SEG_CANVAS, "seg_area_px": area, "path": path})
    # Stage 0a margined-single: all `total` dots on one (larger) canvas, same generator family.
    single_dots = _place(total, SINGLE_CANVAS, rng)
    sfname = f"seg_T{total:02d}_K{nseg}_v{variant}_single_s{seed}.png"
    spath = os.path.join(out_dir, sfname)
    sarea = _draw(single_dots, SINGLE_CANVAS, spath)
    rows.append({"role": "single", "total": total, "nseg": nseg, "variant": variant,
                 "seg_idx": -1, "seg_count": total, "seed": seed,
                 "canvas": SINGLE_CANVAS, "seg_area_px": sarea, "path": spath})
    return rows


# Fixed-cell grid (design):
#   CAP per-segment <= 7 (MAX_PER_SEG), so totals must be reachable: total <= nseg*7.
#   AVOID attractor totals — prior anchor data: 20 and 25 are HARD round-number attractors,
#   so they are BANNED as totals. Use non-round, non-attractor totals (the prior notebook's
#   own clean-control set near 19/21/24/26). 24 retained as the shared anchor cell (non-round,
#   showed no attractor peak in prior data; appears as the 20-30 "0" rows, not a peak).
#
# SINGLE FIXED CELL : the study answers ONE question — does verbal
# interference degrade the count more than non-verbal — which is a WITHIN-configuration
# contrast. So everything (control + all interference arms) uses ONE fixed cell, varied
# only by reps/layouts for statistical power, NOT by a parametric sweep. No N_seg sweep,
# no total sweep. THE CELL: total=24, nseg=4 (per-seg ~6, exact-counting regime; 4 boundaries
# = 4 interference-insertion points). Control for this cell is already collected (T24/K4, 30
# reps, 100% faithful adding). Do NOT add cells without a specific reason.
CELL = (24, 4)
GRID = [CELL]   # the entire grid is one cell, run at many reps
# Standalone small-count baseline : how well do models count an equivalently-sized
# single sub-image holding a SMALL number of dots? = the per-segment-counting floor, the
# comparison point for the multi-segment runs. Default 9 dots (the cap = measured exact ceiling),
# ~10 reps. (Could add 7 too for a second floor point if wanted.)
BASELINE_COUNTS = [9]


def render_baseline(count, variant, seed, out_dir):
    """Standalone small-count single sub-image on the SEGMENT canvas (so it is 'equivalently
    sized' to one segment of the real runs). The per-segment-counting floor / comparison point.
    Returns one manifest row."""
    rng = random.Random((seed * 1000003) ^ (count * 131) ^ (variant * 17) ^ 0xBA5E)
    dots = _place(count, SEG_CANVAS, rng)
    fname = f"baseline_C{count:02d}_v{variant}_s{seed}.png"
    path = os.path.join(out_dir, fname)
    area = _draw(dots, SEG_CANVAS, path)
    return {"role": "baseline", "total": count, "nseg": 1, "variant": variant,
            "seg_idx": 0, "seg_count": count, "seed": seed,
            "canvas": SEG_CANVAS, "seg_area_px": area, "path": path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, help="target total dot count")
    ap.add_argument("--nseg", type=int, help="number of segments to split into")
    ap.add_argument("--reps", type=int, default=20, help="distinct variant layouts per cell (mini-pilot will set final)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="seg_stimuli")
    ap.add_argument("--grid", action="store_true", help="emit the single fixed CELL (total=24, nseg=4) — vary reps for power, not parameters")
    ap.add_argument("--baseline", action="store_true",
                    help="emit the standalone small-count baseline (single seg-sized image, "
                         f"counts={BASELINE_COUNTS}); pair with --reps (~10)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # --- baseline mode: standalone small-count single images, then return ---
    if args.baseline:
        brows = []
        for c in BASELINE_COUNTS:
            for v in range(args.reps):
                brows.append(render_baseline(c, v, args.seed, args.out))
        man = os.path.join(args.out, "manifest.csv")
        with open(man, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["role", "total", "nseg", "variant", "seg_idx",
                                              "seg_count", "seed", "canvas", "seg_area_px", "path"])
            w.writeheader(); w.writerows(brows)
        print(f"Wrote {len(brows)} BASELINE images (counts={BASELINE_COUNTS} x {args.reps} reps) "
              f"-> {args.out}/  (manifest: {man})")
        print("These are the per-segment-counting FLOOR: how well models count a single small-count")
        print("seg-sized image. Compare against multi-segment totals. AI-read only, no parse.")
        return

    cells = []
    if args.grid:
        cells = list(GRID)   # the single fixed CELL (total=24, nseg=4)
    elif args.total and args.nseg:
        cells = [(args.total, args.nseg)]
    else:
        sys.exit("specify --total and --nseg, or --grid (= the one fixed cell), or --baseline")

    rows = []
    for (t, k) in cells:
        for v in range(args.reps):
            rows.append(render_set(t, k, v, args.seed, args.out))
    flat = [r for sub in rows for r in sub]

    man = os.path.join(args.out, "manifest.csv")
    with open(man, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["role", "total", "nseg", "variant", "seg_idx",
                                          "seg_count", "seed", "canvas", "seg_area_px", "path"])
        w.writeheader(); w.writerows(flat)

    n_sets = len(rows)
    n_seg_imgs = sum(1 for r in flat if r["role"] == "segment")
    n_single = sum(1 for r in flat if r["role"] == "single")
    print(f"Wrote {len(flat)} images ({n_seg_imgs} segments + {n_single} margined-singles) "
          f"across {n_sets} sets -> {args.out}/  (manifest: {man})")
    print("CELLS:", ", ".join(f"T{t}/K{k}" for (t, k) in cells), f"x {args.reps} reps")
    print("NEXT: eyeball + AI-read a sample at this canvas size — confirm dots are individually")
    print("      resolvable (no merging) BEFORE a full run. Canvas is small on purpose (cost).")
    print("NOTE: this script renders only. Collection harness is separate + also extractor-free.")


if __name__ == "__main__":
    main()
