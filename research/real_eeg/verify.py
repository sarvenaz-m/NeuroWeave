"""Verify packaged hashes and recompute every held-out metric from predictions."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from .data import load_config, sha256
from .evaluation import evaluate, paired_comparison


def verify_report(root, check_code=False):
    root = Path(root)
    report = json.loads((root / "benchmark.json").read_text(encoding="utf-8"))
    config = load_config(root / "config.json")
    for name, digest in report["artifact_sha256"].items():
        if Path(name).name != name or sha256(root/name) != digest:
            raise ValueError(f"Artifact integrity failure: {name}")
    if check_code:
        for name, digest in report["code_sha256"].items():
            if sha256(Path(name)) != digest:
                raise ValueError(f"Experiment code changed since the recorded run: {name}")
    with (root / "predictions.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len({r["epoch_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate epoch IDs")
    group_for = {str(s): group for group, values in config["subjects"].items() for s in values}
    for row in rows:
        if group_for.get(row["subject"]) != row["split"]:
            raise ValueError("Prediction subject appears in the wrong split")
    for split, details in report["splits"].items():
        subset = [r for r in rows if r["split"] == split]
        if len(subset) != details["epochs"]:
            raise ValueError("Split count mismatch")
        counts = np.bincount([int(r["label"]) for r in subset], minlength=2).tolist()
        if counts != details["class_counts"]:
            raise ValueError("Class count mismatch")
    test_rows = [r for r in rows if r["split"] == "test"]
    y = np.array([int(r["label"]) for r in test_rows])
    subjects = np.array([int(r["subject"]) for r in test_rows])
    recomputed = {}
    for name, expected in report["models"].items():
        probabilities = np.array([[float(r[f"{name}_p_left"]), float(r[f"{name}_p_right"])] for r in test_rows])
        actual = evaluate(y, probabilities, subjects, config["bootstrap"])
        if actual != expected:
            raise ValueError(f"Metric mismatch: {name}")
        recomputed[name] = actual
    for name, expected in report["comparisons"].items():
        actual = paired_comparison(recomputed["cnn_ensemble"], recomputed[name], config["bootstrap"])
        if actual != expected:
            raise ValueError(f"Paired comparison mismatch: {name}")
    for run in report["cnn_runs"]:
        right = np.array([float(r[f"cnn_seed_{run['seed']}_p_right"]) for r in test_rows])
        actual = evaluate(y, np.stack([1-right, right], axis=1), subjects, config["bootstrap"])
        if actual != run["test"]:
            raise ValueError(f"CNN seed metric mismatch: {run['seed']}")
    with (root / "epoch-audit.csv").open(encoding="utf-8", newline="") as handle:
        audit = list(csv.DictReader(handle))
    if len(audit) != report["quality"]["candidate_epochs"]:
        raise ValueError("QC candidate count mismatch")
    accepted = {r["epoch_id"] for r in audit if r["accepted"] == "True"}
    if accepted != {r["epoch_id"] for r in rows}:
        raise ValueError("QC accepted epochs differ from predictions")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="reports/physionet-pilot")
    parser.add_argument("--check-code", action="store_true")
    args = parser.parse_args()
    report = verify_report(args.report_dir, args.check_code)
    print(f"Verified artifact hashes, split isolation, QC and {len(report['models'])} test metric records")


if __name__ == "__main__":
    main()
