"""Compact EEGNet-style CNN and transparent train-fitted reference models.

The CNN follows the temporal/depthwise/separable design of Lawhern et al.
(2018), with an independent PyTorch implementation and a documented v2 setup.
It is not a reproduction of the paper's experiments or reported performance.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from scipy.signal import welch


def bandpower_features(x):
    frequency, power = welch(x, fs=128, nperseg=128, noverlap=64, axis=-1)
    bands = [(8, 12), (12, 20), (20, 30)]
    values = [power[..., (frequency >= low) & (frequency < high)].sum(axis=-1)
              for low, high in bands]
    return np.log(np.maximum(np.stack(values, axis=-1), 1e-12)).reshape(len(x), -1)


def fit_csp(x, y, components):
    """Regularized binary CSP. Fit spatial filters using training trials only."""
    x = np.asarray(x, dtype=np.float64)
    covariance = x @ x.transpose(0, 2, 1)
    covariance /= np.maximum(np.trace(covariance, axis1=1, axis2=2)[:, None, None], 1e-12)
    class_cov = []
    for label in (0, 1):
        if not np.any(y == label):
            raise ValueError("CSP training requires both classes")
        cov = covariance[y == label].mean(axis=0)
        class_cov.append(0.9 * cov + 0.1 * np.eye(x.shape[1]) / x.shape[1])
    _, vectors = eigh(class_cov[0], class_cov[0] + class_cov[1])
    half = components // 2
    return vectors[:, np.r_[np.arange(half), np.arange(x.shape[1]-half, x.shape[1])]].T


def csp_features(x, filters):
    transformed = np.einsum("kc,nct->nkt", filters, x)
    variance = np.var(transformed, axis=-1)
    return np.log(np.maximum(variance / np.maximum(variance.sum(axis=1, keepdims=True), 1e-12), 1e-12))


def sigmoid(logit):
    from scipy.special import expit
    p = expit(logit)
    return np.stack([1-p, p], axis=-1)


def baseline_forward(x, saved):
    """Inference from plain JSON arrays; no pickle or fitting at evaluation."""
    if saved["kind"] == "bandpower_logistic":
        features = bandpower_features(x)
        features = (features - np.array(saved["mean"])) / np.array(saved["scale"])
    elif saved["kind"] == "csp_lda":
        features = csp_features(x, np.array(saved["filters"]))
    else:
        raise ValueError("Unknown baseline")
    return sigmoid(features @ np.array(saved["coef"]) + saved["intercept"])


def make_cnn(dropout=0.5):
    # Lazy import keeps data acquisition and baseline checks independent of torch.
    import torch
    from torch import nn

    class CompactEEGCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.temporal = nn.Conv2d(1, 8, (1, 64), bias=False)
            self.bn1 = nn.BatchNorm2d(8, eps=1e-3, momentum=0.01)
            self.spatial = nn.Conv2d(8, 16, (8, 1), groups=8, bias=False)
            self.bn2 = nn.BatchNorm2d(16, eps=1e-3, momentum=0.01)
            self.depthwise = nn.Conv2d(16, 16, (1, 16), groups=16, bias=False)
            self.pointwise = nn.Conv2d(16, 16, 1, bias=False)
            self.bn3 = nn.BatchNorm2d(16, eps=1e-3, momentum=0.01)
            self.pool1, self.pool2 = nn.AvgPool2d((1, 4)), nn.AvgPool2d((1, 8))
            self.dropout = nn.Dropout(dropout)
            self.classifier = nn.Linear(16 * 8, 2)

        def forward(self, x):
            x = x[:, None]
            x = self.bn1(self.temporal(nn.functional.pad(x, (31, 32, 0, 0))))
            x = self.dropout(self.pool1(nn.functional.elu(self.bn2(self.spatial(x)))))
            x = self.depthwise(nn.functional.pad(x, (7, 8, 0, 0)))
            x = self.dropout(self.pool2(nn.functional.elu(self.bn3(self.pointwise(x)))))
            return self.classifier(x.flatten(1))

        @torch.no_grad()
        def constrain(self):
            for weight, maximum in ((self.spatial.weight, 1.0), (self.classifier.weight, 0.25)):
                norm = weight.flatten(1).norm(dim=1).clamp_min(1e-12)
                weight.mul_((maximum / norm).clamp(max=1).reshape(-1, *([1]*(weight.ndim-1))))

    return CompactEEGCNN()


def cnn_forward(model, x, mean, scale, batch_size=128):
    import torch
    model.eval()
    probabilities = []
    with torch.no_grad():
        for start in range(0, len(x), batch_size):
            batch = torch.from_numpy(((x[start:start+batch_size] - mean) / scale).astype(np.float32))
            probabilities.append(model(batch).softmax(dim=1).numpy())
    return np.concatenate(probabilities)
