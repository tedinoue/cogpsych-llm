#!/usr/bin/env python3
"""Three-model modal-vs-true comparison (the decisive anchoring figure).
Reads the AI-read JSONs only."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

files = [("anchor_grok_read.json", "#c0392b", "Grok (xAI)"),
         ("anchor_gemini_read.json", "#2980b9", "Gemini (Google)"),
         ("anchor_llama_read.json", "#27ae60", "Llama (Meta)")]
fig, (axm, axM) = plt.subplots(1, 2, figsize=(15, 6.5))
for fn, color, label in files:
    d = json.load(open(fn))
    ans = {int(k): v for k, v in d["answers"].items()}
    ns = sorted(ans)
    means = [sum(ans[N]) / len(ans[N]) for N in ns]
    modals = [max(set(ans[N]), key=ans[N].count) for N in ns]
    axm.plot(ns, modals, "s-", color=color, lw=1.8, label=label, alpha=0.85)
    axM.plot(ns, means, "o-", color=color, lw=1.8, label=label, alpha=0.85)
for ax, title in [(axm, "MODAL response vs true count"), (axM, "MEAN response vs true count")]:
    ns = list(range(25, 41))
    ax.plot(ns, ns, "k--", lw=1, alpha=0.5, label="true (perfect)")
    for rn in [25, 30, 35, 40]:
        ax.axhline(rn, color="gray", ls=":", lw=0.5, alpha=0.4)
    ax.set_xlabel("true count"); ax.set_ylabel("reported count")
    ax.set_title(title); ax.legend(fontsize=9); ax.grid(alpha=0.2)
fig.suptitle("Round-number anchoring across three labs — all anchor, differing in strength\n"
             "Each model's MODAL answer locks onto values and steps between them (a staircase, not a ramp).\n"
             "Red lines mark multiples of 5. Grok: widest capture (25 held N=25-35). Gemini: 26→30→35. Llama: noisy, locks to 40.",
             fontsize=11)
plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.savefig("anchor_three_model.png", dpi=120)
print("wrote anchor_three_model.png")
