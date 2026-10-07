"""Run the complete subject-independent benchmark; CPU execution is supported."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import platform
import random
from pathlib import Path
import time

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .data import CHANNELS, CLASSES, CHECKSUM_SHA256, build_dataset, load_config, sha256, write_json
from .evaluation import evaluate, paired_comparison, subject_macro_score
from .models import bandpower_features, baseline_forward, cnn_forward, csp_features, fit_csp, make_cnn


def fit_baselines(x, y, subjects, masks, output):
    train, validation = masks["train"], masks["validation"]
    features = bandpower_features(x)
    scaler = StandardScaler().fit(features[train])
    normalized = scaler.transform(features)
    candidates = []
    for strength in (0.01, 0.1, 1.0, 10.0):
        model = LogisticRegression(C=strength, class_weight="balanced", solver="lbfgs", max_iter=2000)
        model.fit(normalized[train], y[train])
        score = subject_macro_score(y[validation], model.predict_proba(normalized[validation]), subjects[validation])
        candidates.append((score, strength, model))
    score, strength, model = max(candidates, key=lambda r: r[0])
    bandpower = {"kind": "bandpower_logistic", "classes": list(CLASSES), "C": strength,
                 "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                 "coef": model.coef_[0].tolist(), "intercept": float(model.intercept_[0]),
                 "validation_candidates": [{"C": r[1], "subject_macro_balanced_accuracy": r[0]} for r in candidates]}
    candidates = []
    for components in (2, 4, 6):
        filters = fit_csp(x[train], y[train], components)
        features = csp_features(x, filters)
        model = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        model.fit(features[train], y[train])
        score = subject_macro_score(y[validation], model.predict_proba(features[validation]), subjects[validation])
        candidates.append((score, components, filters, model))
    score, components, filters, model = max(candidates, key=lambda r: r[0])
    csp = {"kind": "csp_lda", "classes": list(CLASSES), "components": components,
           "covariance_shrinkage": 0.1, "lda_shrinkage": "auto", "filters": filters.tolist(),
           "coef": model.coef_[0].tolist(), "intercept": float(model.intercept_[0]),
           "validation_candidates": [{"components": r[1], "subject_macro_balanced_accuracy": r[0]} for r in candidates]}
    write_json(output / "bandpower-logistic.json", bandpower)
    write_json(output / "csp-lda.json", csp)
    return {"bandpower_logistic": baseline_forward(x, bandpower), "csp_lda": baseline_forward(x, csp)}


def fit_cnn(x, y, masks, config, output):
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    train, validation = masks["train"], masks["validation"]
    # Fit channel statistics to the training people only, then freeze them.
    mean = x[train].mean(axis=(0, 2), keepdims=True)
    scale = np.maximum(x[train].std(axis=(0, 2), keepdims=True), 1e-6)
    settings = config["training"]
    write_json(output / "cnn-normalization.json", {"mean": mean.tolist(), "scale": scale.tolist(),
               "fit_split": "train", "channels": list(CHANNELS), "input_shape": [8, 256],
               "architecture": "CompactEEGCNN", "dropout": settings["dropout"], "classes": list(CLASSES)})
    xt = torch.from_numpy(((x[train] - mean) / scale).astype(np.float32))
    yt = torch.from_numpy(y[train].astype(np.int64))
    xv = torch.from_numpy(((x[validation] - mean) / scale).astype(np.float32))
    yv = torch.from_numpy(y[validation].astype(np.int64))
    counts = np.bincount(y[train], minlength=2)
    weights = torch.tensor(len(yt) / (2*counts), dtype=torch.float32)
    seed_probabilities, runs = [], []
    for seed in settings["seeds"]:
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        model = make_cnn(settings["dropout"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=settings["learning_rate"],
                                      weight_decay=settings["weight_decay"])
        loader = DataLoader(TensorDataset(xt, yt), batch_size=settings["batch_size"], shuffle=True,
                            generator=torch.Generator().manual_seed(seed), num_workers=0)
        criterion = nn.CrossEntropyLoss(weight=weights)
        best_loss, best_state, best_epoch, stale, history = float("inf"), None, 0, 0, []
        started = time.perf_counter()
        for epoch in range(1, settings["epochs"]+1):
            model.train(); total = 0.0
            for batch, labels in loader:
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(batch), labels)
                loss.backward(); optimizer.step(); model.constrain()
                total += loss.item() * len(labels)
            model.eval()
            with torch.no_grad():
                logits = model(xv)
                val_loss = nn.functional.cross_entropy(logits, yv).item()
                val_accuracy = (logits.argmax(dim=1) == yv).float().mean().item()
            history.append({"epoch": epoch, "train_loss": total/len(yt),
                            "validation_loss": val_loss, "validation_accuracy": val_accuracy})
            if val_loss < best_loss - 1e-6:
                best_loss, best_epoch, stale = val_loss, epoch, 0
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            else:
                stale += 1
            if epoch == 1 or epoch % 10 == 0:
                print(f"CNN seed {seed} epoch {epoch}: validation loss {val_loss:.4f}", flush=True)
            if stale >= settings["patience"]:
                break
        model.load_state_dict(best_state)
        model.eval()
        checkpoint = output / f"cnn-seed-{seed}.pt"
        torch.save(best_state, checkpoint)
        probabilities = cnn_forward(model, x, mean, scale)
        seed_probabilities.append(probabilities)
        runs.append({"seed": seed, "selected_epoch": best_epoch,
                     "selected_validation_loss": best_loss, "epochs_run": len(history),
                     "parameters": sum(p.numel() for p in model.parameters()),
                     "train_seconds": time.perf_counter()-started, "history": history,
                     "checkpoint": checkpoint.name, "checkpoint_sha256": sha256(checkpoint)})
    return np.mean(seed_probabilities, axis=0), seed_probabilities, runs


def write_csv(path, rows):
    if not rows:
        raise ValueError("Cannot export an empty table")
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/physionet-pilot.json")
    parser.add_argument("--data-dir", default="data/physionet")
    parser.add_argument("--output", default="reports/physionet-pilot")
    args = parser.parse_args()
    config, output = load_config(args.config), Path(args.output)
    # A new directory prevents accidentally mixing artifacts from different runs.
    if output.exists() and any(output.iterdir()):
        parser.error("Output is not empty; choose a new --output directory for a new run")
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    x, y, subjects, splits, metadata, audit, files = build_dataset(config, args.data_dir)
    masks = {name: splits == name for name in config["subjects"]}
    probabilities = fit_baselines(x, y, subjects, masks, output)
    ensemble, individual, cnn_runs = fit_cnn(x, y, masks, config, output)
    probabilities["cnn_ensemble"] = ensemble
    test = masks["test"]
    metrics = {name: evaluate(y[test], p[test], subjects[test], config["bootstrap"])
               for name, p in probabilities.items()}
    seed_metrics = [evaluate(y[test], p[test], subjects[test], config["bootstrap"]) for p in individual]
    for run, metric in zip(cnn_runs, seed_metrics):
        run["test"] = metric
    prediction_rows = []
    for index, row in enumerate(metadata):
        item = {"epoch_id": row["epoch_id"], "subject": row["subject"], "run": row["run"],
                "split": row["split"], "label": row["label"], "onset_s": row["onset_s"]}
        for name, p in probabilities.items():
            item[f"{name}_p_left"] = float(p[index, 0]); item[f"{name}_p_right"] = float(p[index, 1])
        for seed, p in zip(config["training"]["seeds"], individual):
            item[f"cnn_seed_{seed}_p_right"] = float(p[index, 1])
        prediction_rows.append(item)
    write_csv(output / "predictions.csv", prediction_rows)
    write_csv(output / "epoch-audit.csv", [{**r, "reasons": ";".join(r["reasons"])} for r in audit])
    write_json(output / "config.json", config)
    write_json(output / "source-manifest.json", {"dataset": config["dataset"], "license": "ODC-By-1.0",
               "checksum_index_sha256": CHECKSUM_SHA256, "files": files})
    # One public trial illustrates the preprocessing contract; it is not a training cache.
    example_index = next(i for i, r in enumerate(metadata) if r["subject"] == min(subjects))
    example = {"schema_version": 1, "source": "physionet-eegmmidb", "sampling_rate_hz": 128,
               "units": "microvolts", "channels": list(CHANNELS), "samples": x[example_index].tolist(),
               "provenance": metadata[example_index], "dataset_doi": "10.13026/C28G6P",
               "license": "ODC-By-1.0", "preprocessing": config["preprocessing"]}
    write_json(output / "example-real-window.json", example)
    import mne, scipy, sklearn, torch
    report = {"schema_version": 2, "software_version": "2.0.0", "experiment": config["name"],
              "created_at_utc": datetime.now(timezone.utc).isoformat(), "data_kind": "real_recorded_eeg",
              "dataset": {"name": "PhysioNet EEG Motor Movement/Imagery Dataset", "version": "1.0.0",
                          "doi": "10.13026/C28G6P", "runs": config["runs"], "classes": list(CLASSES)},
              "selection": "First 36 numbered public subjects, split permutation fixed before training" if "pilot" in config["name"] else "All 109 numbered public subjects; strict EDF and epoch quality checks",
              "splits": {name: {"subjects": config["subjects"][name], "epochs": int(mask.sum()),
                                  "class_counts": np.bincount(y[mask], minlength=2).tolist()}
                         for name, mask in masks.items()},
              "quality": {"candidate_epochs": len(audit), "accepted_epochs": len(x),
                          "rejected_epochs": len(audit)-len(x), "raw_files": len(files),
                          "by_split": {name: {"accepted": int(mask.sum()),
                                             "rejected": sum(not row["accepted"] for row in audit if row["split"] == name)}
                                       for name, mask in masks.items()}},
              "preprocessing": config["preprocessing"], "training": config["training"],
              "primary_metric": "subject_macro_balanced_accuracy",
              "decision_rule": "Argmax probabilities; ties resolve to left class; no test tuning",
              "bootstrap": {**config["bootstrap"], "unit": "subject", "method": "percentile"},
              "models": metrics, "cnn_runs": cnn_runs,
              "comparisons": {name: paired_comparison(metrics["cnn_ensemble"], metrics[name], config["bootstrap"])
                              for name in ("bandpower_logistic", "csp_lda")},
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
                              "mne": mne.__version__, "torch": torch.__version__, "device": "cpu", "torch_threads": 2},
              "elapsed_seconds": time.perf_counter()-started,
              "limitations": ["One fixed subject split and a small six-person test cohort in the pilot",
                              "CNN seeds measure initialization sensitivity, not independent test cohorts",
                              "Offline acausal filtering; performance is not a streaming benchmark",
                              "No externally calibrated probabilities or independent dataset validation",
                              "Test QC coverage is reported; no claim of clinical or usability validation"]}
    code_paths = sorted(Path("research/real_eeg").glob("*.py"))
    report["code_sha256"] = {str(p): sha256(p) for p in code_paths}
    report["artifact_sha256"] = {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}
    write_json(output / "benchmark.json", report)
    for name, metric in metrics.items():
        print(name, f"subject balanced accuracy {metric['subject_macro_balanced_accuracy']:.4f}",
              "95% CI", metric["subject_bootstrap_95_ci"])


if __name__ == "__main__":
    main()
