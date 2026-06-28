#!/usr/bin/env python3
"""Render round-number-anchoring histograms from AI-READ answer values.
Input: anchor_<model>_read.json (the values a human/AI extracted by reading raw.jsonl).
This script ONLY visualizes already-read values; it never parses model output.
"""
import json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

infile = sys.argv[1]
outfile = sys.argv[2]
d = json.load(open(infile))
ans = {int(k): v for k, v in d["answers"].items()}
true_ns = sorted(ans)
model = d["model"]

# response range for x-axis
allv = [x for v in ans.values() for x in v]
lo, hi = min(allv + [25]), max(allv + [40])
xr = list(range(lo, hi + 1))
rounds = set(range(0, 100, 5))  # multiples of 5

fig, axes = plt.subplots(4, 4, figsize=(16, 12), sharex=True)
axes = axes.flatten()
for i, N in enumerate(true_ns):
    ax = axes[i]
    vals = ans[N]
    counts = [vals.count(x) for x in xr]
    colors = ["#c0392b" if x in rounds else "#7f8c8d" for x in xr]  # red = multiple of 5
    ax.bar(xr, counts, color=colors, width=0.9)
    ax.axvline(N, color="#2980b9", ls="--", lw=1.5)  # true value (blue dashed)
    mean = sum(vals) / len(vals)
    ax.axvline(mean, color="#27ae60", ls="-", lw=1.0, alpha=0.7)  # mean (green)
    pct_round = 100 * sum(1 for v in vals if v in rounds) / len(vals)
    is_round_N = N in rounds
    ax.set_title(f"true N = {N}" + ("  (round)" if is_round_N else ""),
                 fontsize=10, fontweight=("bold" if is_round_N else "normal"))
    ax.text(0.02, 0.92, f"mean {mean:.1f}\n{pct_round:.0f}% on ×5", transform=ax.transAxes,
            fontsize=8, va="top", ha="left",
            bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))
    ax.set_yticks([])
for j in range(len(true_ns), len(axes)):
    axes[j].axis("off")
fig.suptitle(f"Round-number anchoring — {model}\n"
             f"response histograms by true count (red = multiple of 5, blue dashed = true N, green = mean)",
             fontsize=14)
fig.text(0.5, 0.04, "model's reported count", ha="center", fontsize=11)
plt.tight_layout(rect=[0, 0.05, 1, 0.96])
plt.savefig(outfile, dpi=110)
print(f"wrote {outfile}")

# also print the clean metric table to stdout
print(f"\n{model} — anchoring metric:")
print("true_N | mean | modal | % answers on a multiple of 5 | round-N?")
for N in true_ns:
    vals = ans[N]
    mean = sum(vals) / len(vals)
    modal = max(set(vals), key=vals.count)  # the single most common answer
    pct = 100 * sum(1 for v in vals if v in rounds) / len(vals)
    print(f"  {N:4d} | {mean:5.1f} | {modal:5d} | {pct:5.0f}% | {'ROUND' if N in rounds else ''}")

# the DECISIVE plot: mean response vs true N. Staircase = anchoring; diagonal = honest.
fig2, ax2 = plt.subplots(figsize=(8, 7))
means = [sum(ans[N]) / len(ans[N]) for N in true_ns]
modals = [max(set(ans[N]), key=ans[N].count) for N in true_ns]
ax2.plot(true_ns, true_ns, color="#2980b9", ls="--", lw=1.5, label="true (perfect estimation)")
ax2.plot(true_ns, means, "o-", color="#27ae60", lw=2, label="mean response")
ax2.plot(true_ns, modals, "s:", color="#c0392b", lw=1.5, alpha=0.8, label="modal response")
for rn in [25, 30, 35, 40]:
    ax2.axhline(rn, color="#c0392b", ls=":", lw=0.6, alpha=0.4)
ax2.set_xlabel("true count"); ax2.set_ylabel("model's reported count")
ax2.set_title(f"Mean & modal response vs. true count — {model}\n"
              "flat steps near 25/30/35/40 = anchoring;  following the dashed line = honest estimation")
ax2.legend(); ax2.grid(alpha=0.2)
out2 = outfile.replace(".png", "_curve.png")
plt.tight_layout(); plt.savefig(out2, dpi=110)
print(f"wrote {out2}")
