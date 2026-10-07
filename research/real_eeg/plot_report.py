"""Render scientific figures directly from a verified recorded EEG report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .verify import verify_report

NAMES = {"bandpower_logistic": "Band power + logistic", "csp_lda": "CSP + shrinkage LDA",
         "cnn_ensemble": "CNN · 3 seeds"}
COLORS = ["#6b9cff", "#91d7f2", "#ff9858"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="reports/physionet-pilot")
    parser.add_argument("--media-dir", default="docs/media")
    args = parser.parse_args()
    root, media = Path(args.report_dir), Path(args.media_dir)
    report = verify_report(root)
    media.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "figure.facecolor": "#080d18",
                         "axes.facecolor": "#111b2c", "axes.edgecolor": "#41516b", "axes.labelcolor": "#dce5f8",
                         "text.color": "#dce5f8", "xtick.color": "#b7c4d8", "ytick.color": "#b7c4d8",
                         "grid.color": "#293951", "savefig.facecolor": "#080d18"})
    fig = plt.figure(figsize=(14, 8), layout="constrained")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.2, 1])
    ax = fig.add_subplot(grid[0, :2]); keys = list(NAMES)
    means = np.array([report["models"][k]["subject_macro_balanced_accuracy"] for k in keys])
    intervals = np.array([report["models"][k]["subject_bootstrap_95_ci"] for k in keys])
    ax.bar(np.arange(3), means, color=COLORS, width=0.55)
    ax.errorbar(np.arange(3), means, yerr=[means-intervals[:, 0], intervals[:, 1]-means],
                fmt="none", ecolor="#dce5f8", capsize=6)
    ax.axhline(0.5, color="#b7c4d8", linestyle="--", linewidth=1, label="Binary chance reference")
    ax.set(ylim=(0, 1), ylabel="Subject mean balanced accuracy", xticks=np.arange(3),
           xticklabels=[NAMES[k] for k in keys], title="Held-out participants · 95% participant bootstrap intervals")
    ax.grid(axis="y", alpha=0.5); ax.set_axisbelow(True)
    for i, value in enumerate(means): ax.text(i, 0.06, f"{value*100:.1f}%", ha="center", color="#080d18", weight="bold")
    ax = fig.add_subplot(grid[0, 2])
    for i, key in enumerate(keys):
        rows = report["models"][key]["per_subject"]
        ax.plot(np.arange(len(rows)), [r["balanced_accuracy"] for r in rows], marker="o", color=COLORS[i], label=NAMES[key])
    ax.set(ylim=(0, 1), xticks=np.arange(len(rows)), xticklabels=[f"S{r['subject']:03d}" for r in rows],
           ylabel="Balanced accuracy", title="Individual test participants")
    ax.tick_params(axis="x", rotation=45); ax.grid(alpha=0.5); ax.legend(fontsize=7, loc="lower right")
    for i, key in enumerate(keys):
        ax = fig.add_subplot(grid[1, i]); cm = np.array(report["models"][key]["confusion_matrix"])
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(1, cm.max()))
        for a in range(2):
            for b in range(2): ax.text(b, a, str(cm[a, b]), ha="center", va="center", color="#080d18" if cm[a, b] < cm.max()/2 else "white", fontsize=20, weight="bold")
        ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Left", "Right"], yticklabels=["Left", "Right"],
               xlabel="Predicted imagery", ylabel="Recorded cue", title=NAMES[key])
    total = sum(len(s["subjects"]) for s in report["splits"].values())
    test = report["splits"]["test"]
    fig.suptitle(f"NeuroWeave 2 / REAL EEG\nPhysioNet · {total} participants · {len(test['subjects'])} unseen test participants · {test['epochs']} test trials", fontsize=17, weight="bold")
    fig.savefig(media/"real-eeg-benchmark.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
    for run, color in zip(report["cnn_runs"], COLORS):
        history = run["history"]
        for ax, key, title in zip(axes, ["train_loss", "validation_loss"], ["Training loss", "Validation loss"]):
            ax.plot([r["epoch"] for r in history], [r[key] for r in history], color=color, label=f"Seed {run['seed']}")
            ax.axvline(run["selected_epoch"], color=color, alpha=0.3, linestyle="--")
            ax.set(title=title, xlabel="Epoch", ylabel="Cross-entropy"); ax.grid(alpha=0.5)
    axes[1].legend(fontsize=8); fig.suptitle("CNN checkpoint selection uses validation loss only", fontsize=14)
    fig.savefig(media/"real-eeg-learning.png", dpi=180); plt.close(fig)
    example = json.loads((root/"example-real-window.json").read_text())
    fig, axes = plt.subplots(8, 1, figsize=(12, 7), sharex=True, layout="constrained")
    for i, (ax, channel, values) in enumerate(zip(axes, example["channels"], example["samples"])):
        ax.plot(np.arange(256)/128, values, color=COLORS[i % 3], linewidth=0.8)
        ax.set_ylabel(channel+"\nµV", rotation=0, labelpad=22); ax.grid(alpha=0.4)
    axes[-1].set_xlabel("Time within processed epoch (s)")
    provenance = example["provenance"]
    fig.suptitle(f"Recorded EEG / {provenance['epoch_id']} / {provenance['split']} example\nCommon average · 1–40 Hz offline filter · 128 Hz · public PhysioNet data", fontsize=13)
    fig.savefig(media/"real-eeg-trace.png", dpi=180); plt.close(fig)
    print("Rendered verified benchmark, learning curves and recorded EEG trace")


if __name__ == "__main__":
    main()
