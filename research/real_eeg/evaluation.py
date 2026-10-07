"""Trial metrics and uncertainty with the participant as the resampling unit."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score


def subject_scores(y, probabilities, subjects):
    predicted = probabilities.argmax(axis=1)
    return [{"subject": int(s), "n": int(np.sum(subjects == s)),
             "balanced_accuracy": float(balanced_accuracy_score(y[subjects == s], predicted[subjects == s]))}
            for s in sorted(set(subjects))]


def subject_macro_score(y, probabilities, subjects):
    return float(np.mean([r["balanced_accuracy"] for r in subject_scores(y, probabilities, subjects)]))


def bootstrap_mean(values, iterations=5000, seed=2026):
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("At least two finite subject scores are required")
    rng = np.random.default_rng(seed)
    sampled = values[rng.integers(0, len(values), size=(iterations, len(values)))].mean(axis=1)
    return [float(v) for v in np.quantile(sampled, [0.025, 0.975])]


def evaluate(y, probabilities, subjects, bootstrap):
    if probabilities.shape != (len(y), 2) or not np.isfinite(probabilities).all():
        raise ValueError("Invalid class probabilities")
    if np.any(probabilities < 0) or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-6):
        raise ValueError("Class probabilities must sum to one")
    predicted = probabilities.argmax(axis=1)
    rows = subject_scores(y, probabilities, subjects)
    values = [r["balanced_accuracy"] for r in rows]
    return {"n": len(y), "subjects": len(rows),
            "accuracy": float(accuracy_score(y, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
            "subject_macro_balanced_accuracy": float(np.mean(values)),
            "subject_bootstrap_95_ci": bootstrap_mean(values, **bootstrap),
            "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)),
            "roc_auc": float(roc_auc_score(y, probabilities[:, 1])),
            "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
            "per_subject": rows}


def paired_comparison(first, second, bootstrap):
    left = {r["subject"]: r["balanced_accuracy"] for r in first["per_subject"]}
    right = {r["subject"]: r["balanced_accuracy"] for r in second["per_subject"]}
    if left.keys() != right.keys():
        raise ValueError("Paired models must use the same test subjects")
    differences = [left[s] - right[s] for s in sorted(left)]
    return {"mean_difference": float(np.mean(differences)),
            "paired_subject_bootstrap_95_ci": bootstrap_mean(differences, **bootstrap),
            "interpretation": "Exploratory participant-level comparison on this fixed split"}
