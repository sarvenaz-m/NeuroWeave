"""Synthetic EEG benchmark and a fully trainable temporal CNN in NumPy.

Research implementation with explicit synthetic-data provenance.
All generated recordings are artificial. No medical interpretation is supported.
"""
from __future__ import annotations
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

FS, CHANNELS, SAMPLES = 128, 8, 256


def quality(x):
    x = np.asarray(x, dtype=float)
    if x.shape != (CHANNELS, SAMPLES) or not np.isfinite(x).all():
        return {"usable": False, "reasons": ["Invalid shape or non-finite samples"]}
    reasons = []
    if np.any(x.std(axis=1) < .5):
        reasons.append("Flat channel")
    if np.max(np.abs(x)) > 150:
        reasons.append("Amplitude exceeds demo threshold")
    return {"usable": not reasons, "reasons": reasons}


def preprocess(x):
    """Per-window channel centring, fixed 20 uV scale. No fitted statistics."""
    x = np.asarray(x, dtype=float)
    if x.shape[-2:] != (CHANNELS, SAMPLES) or not np.isfinite(x).all():
        raise ValueError("Expected finite [..., 8, 256] array")
    return (x - x.mean(axis=-1, keepdims=True)) / 20.


def spectrum(x):
    """One-sided Hann periodogram in uV²/Hz, averaged across channels."""
    x = np.asarray(x, dtype=float)
    w = .5 - .5 * np.cos(2 * np.pi * np.arange(SAMPLES) / SAMPLES)
    centred = x - x.mean(axis=-1, keepdims=True)
    p = np.abs(np.fft.rfft(centred * w, axis=-1)) ** 2 / (FS * (w*w).sum())
    p[..., 1:-1] *= 2
    return np.fft.rfftfreq(SAMPLES, 1/FS), p.mean(axis=-2)


def band_feature(x):
    f, p = spectrum(x)
    a = p[..., (f >= 8) & (f < 13)].sum(axis=-1) * FS / SAMPLES
    b = p[..., (f >= 13) & (f <= 30)].sum(axis=-1) * FS / SAMPLES
    return np.log((b + 1e-8) / (a + 1e-8))


def dataset(seed=144, subjects=18, windows=32):
    """Two artificial frequency conditions with virtual-subject nuisance factors.

    The same nuisance distribution is used for both labels. Conditions A and B
    have 10 Hz and 20 Hz dominant components. They are NOT brain states.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(SAMPLES) / FS
    xs, ys, ids = [], [], []
    for subject in range(subjects):
        gains = rng.uniform(.65, 1.35, (CHANNELS, 1))
        offsets = rng.normal(0, 3, (CHANNELS, 1))
        drift = rng.uniform(.15, .8)
        for i in range(windows):
            label = i % 2
            freq = (10 if label == 0 else 20) + rng.normal(0, .45)
            phase = rng.uniform(0, 2*np.pi, (CHANNELS, 1))
            amplitude = rng.uniform(9, 19)
            wave = amplitude*np.sin(2*np.pi*freq*t + phase)
            background = 3*np.sin(2*np.pi*(20 if label == 0 else 10)*t + phase*.7)
            noise = rng.normal(0, rng.uniform(3, 7), (CHANNELS, SAMPLES))
            slow = 4*np.sin(2*np.pi*drift*t + phase)
            xs.append(gains*(wave + background) + noise + slow + offsets)
            ys.append(label)
            ids.append(f"virtual-{subject+1:02d}")
    return np.asarray(xs), np.asarray(ys), np.asarray(ids)


def split_subjects(ids):
    names = sorted(set(ids))
    if len(names) != 18:
        raise ValueError("Benchmark expects 18 virtual subjects")
    groups = {"train": names[:12], "validation": names[12:15], "test": names[15:]}
    return {key: np.isin(ids, val) for key, val in groups.items()}, groups


class TinyCNN:
    """8 -> 8 valid temporal filters, K=17, stride=4, ReLU, GAP, 2 logits."""
    def __init__(self, seed=144):
        rng = np.random.default_rng(seed)
        self.p = {"kernel": rng.normal(0, np.sqrt(2/(8*17)), (8, 8, 17)),
                  "bias": np.zeros(8), "head": rng.normal(0, .15, (8, 2)),
                  "head_bias": np.zeros(2)}

    def forward(self, x, cache=False):
        patches = sliding_window_view(x, 17, axis=-1)[:, :, ::4, :]
        z = np.einsum('bctk,ock->bot', patches, self.p['kernel'], optimize=True)
        z += self.p['bias'][None, :, None]
        pooled = np.maximum(z, 0).mean(axis=-1)
        logits = pooled @ self.p['head'] + self.p['head_bias']
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        return (probs, (patches, z, pooled)) if cache else probs

    def loss_grad(self, x, y):
        probs, (patches, z, pooled) = self.forward(x, cache=True)
        loss = -np.log(probs[np.arange(len(y)), y] + 1e-12).mean()
        d = probs.copy()
        d[np.arange(len(y)), y] -= 1
        d /= len(y)
        dz = (d @ self.p['head'].T)[:, :, None] * (z > 0) / z.shape[-1]
        grads = {"head": pooled.T @ d, "head_bias": d.sum(axis=0),
                 "kernel": np.einsum('bot,bctk->ock', dz, patches, optimize=True),
                 "bias": dz.sum(axis=(0, 2))}
        return float(loss), grads


def metrics(y, prediction):
    cm = np.zeros((2, 2), dtype=int)
    for a, b in zip(y, prediction):
        cm[a, b] += 1
    recall = np.diag(cm) / np.maximum(cm.sum(axis=1), 1)
    return {"balanced_accuracy": float(recall.mean()),
            "accuracy": float((y == prediction).mean()),
            "confusion_matrix": cm.tolist(), "n": len(y)}
