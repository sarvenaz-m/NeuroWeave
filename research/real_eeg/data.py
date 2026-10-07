"""Verified EDF acquisition and deterministic, label-independent preprocessing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt

BASE_URL = "https://physionet.org/files/eegmmidb/1.0.0/"
CHECKSUM_SHA256 = "7f5d16957d8ee7bce86cc7ccba0e5994f63f33781607eb3f838392d49311a208"
RUNS = (4, 8, 12)
CHANNELS = ("FC3", "FC4", "C3", "Cz", "C4", "CP3", "CPz", "CP4")
CLASSES = ("left_fist_imagery", "right_fist_imagery")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("dataset") != "eegmmidb-1.0.0":
        raise ValueError("This adapter only supports EEGMMIDB version 1.0.0")
    if tuple(config.get("runs", [])) != RUNS:
        raise ValueError("Left/right imagery requires exactly runs 4, 8 and 12")
    groups = config.get("subjects", {})
    if set(groups) != {"train", "validation", "test"}:
        raise ValueError("Declare train, validation and test subjects explicitly")
    all_ids = []
    for key in ("train", "validation", "test"):
        values = groups[key]
        if not values or any(type(v) is not int or not 1 <= v <= 109 for v in values):
            raise ValueError(f"Invalid or empty {key} subject list")
        all_ids.extend(values)
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("Subject groups contain duplicates or overlap")
    expected = {"channels": list(CHANNELS), "source_fs": 160, "target_fs": 128,
                "epoch_start_s": 1.0, "epoch_duration_s": 2.0,
                "bandpass_hz": [1.0, 40.0], "filter_order": 4,
                "reference": "common_average_64", "max_peak_to_peak_uv": 500.0,
                "min_channel_std_uv": 0.1}
    if config.get("preprocessing") != expected:
        raise ValueError("Unsupported preprocessing; use the documented v2 contract")
    return config


def file_inventory(config):
    return [f"S{s:03d}/S{s:03d}R{r:02d}.edf"
            for s in sorted(sum(config["subjects"].values(), [])) for r in RUNS]


def read_checksums(path):
    if sha256(path) != CHECKSUM_SHA256:
        raise ValueError("Official checksum index differs from the pinned version")
    result = {}
    for line in Path(path).read_text(encoding="ascii").splitlines():
        digest, name = line.split(maxsplit=1)
        result[name.lstrip("*")] = digest
    return result


def preprocess_recording(samples_uv, fs, config):
    """Reference and bandpass a continuous 64-channel recording.

    Input is all 64 channels in canonical EDF order. Reference/filter operate
    within a recording, never across people or train/validation/test groups.
    Filtering is offline and uses future samples within that same recording.
    """
    pp = config["preprocessing"]
    data = np.asarray(samples_uv, dtype=np.float64)
    if data.ndim != 2 or data.shape[0] != 64 or not np.isfinite(data).all():
        raise ValueError("Expected finite 64-channel EEG in microvolts")
    if fs != pp["source_fs"]:
        raise ValueError(f"Unsupported EDF sample rate: {fs}")
    referenced = data - data.mean(axis=0, keepdims=True)
    sos = butter(pp["filter_order"], pp["bandpass_hz"], btype="bandpass", fs=fs, output="sos")
    filtered = sosfiltfilt(sos, referenced, axis=-1)
    return filtered


def extract_epochs(filtered_uv, channel_names, annotations, config):
    pp = config["preprocessing"]
    if len(set(channel_names)) != 64:
        raise ValueError("Expected 64 unique EEG channel names")
    lookup = {name.casefold(): i for i, name in enumerate(channel_names)}
    try:
        picked = filtered_uv[[lookup[name.casefold()] for name in CHANNELS]]
    except KeyError as error:
        raise ValueError(f"Required motor channel missing: {error}") from error
    accepted, rows = [], []
    previous_end = -1
    for event_index, (onset, duration, description) in enumerate(annotations):
        if description not in ("T1", "T2"):
            continue
        start_s = float(onset) + pp["epoch_start_s"]
        start = int(round(start_s * 160))
        end = start + 320
        reasons = []
        if duration < pp["epoch_start_s"] + pp["epoch_duration_s"]:
            reasons.append("annotation_too_short")
        if start < 0 or end > picked.shape[1]:
            reasons.append("outside_recording")
        if start < previous_end:
            reasons.append("overlapping_event")
        previous_end = max(previous_end, end)
        epoch = None
        if not reasons:
            epoch = resample_poly(picked[:, start:end], 4, 5, axis=-1)
            epoch -= epoch.mean(axis=-1, keepdims=True)
            if np.any(np.ptp(epoch, axis=-1) > pp["max_peak_to_peak_uv"]):
                reasons.append("peak_to_peak_gt_500_uv")
            if np.any(epoch.std(axis=-1) < pp["min_channel_std_uv"]):
                reasons.append("channel_std_lt_0.1_uv")
        row = {"event_index": event_index, "onset_s": float(onset),
               "duration_s": float(duration), "epoch_start_s": start_s,
               "label": 0 if description == "T1" else 1,
               "accepted": not reasons, "reasons": reasons}
        if not reasons:
            if epoch.shape != (8, 256) or not np.isfinite(epoch).all():
                raise ValueError("Invalid processed epoch")
            accepted.append(epoch.astype(np.float32))
        rows.append(row)
    return accepted, rows


def build_dataset(config, data_dir):
    """Re-read and verify every EDF; do not accept a stale processed cache."""
    import mne

    data_dir = Path(data_dir)
    checksums = read_checksums(data_dir / "SHA256SUMS.txt")
    xs, ys, ids, groups, metadata, audit, files = [], [], [], [], [], [], []
    group_for = {s: name for name, values in config["subjects"].items() for s in values}
    for name in file_inventory(config):
        path = data_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing {name}; run research.real_eeg.download first")
        digest = sha256(path)
        if checksums.get(name) != digest:
            raise ValueError(f"SHA-256 mismatch for {name}; re-download it")
        subject, run = int(name[1:4]), int(name[-6:-4])
        raw = mne.io.read_raw_edf(path, preload=True, verbose="ERROR")
        mne.datasets.eegbci.standardize(raw)
        if len(raw.ch_names) != 64:
            raise ValueError(f"{name}: expected 64 EEG channels")
        annotations = list(zip(raw.annotations.onset, raw.annotations.duration,
                               raw.annotations.description))
        filtered = preprocess_recording(raw.get_data() * 1e6, raw.info["sfreq"], config)
        epochs, rows = extract_epochs(filtered, raw.ch_names, annotations, config)
        file_row = {"path": name, "url": BASE_URL + name, "sha256": digest,
                    "bytes": path.stat().st_size, "subject": subject, "run": run,
                    "accepted": len(epochs), "rejected": len(rows) - len(epochs)}
        files.append(file_row)
        epoch_iter = iter(epochs)
        for row in rows:
            row.update(subject=subject, run=run, split=group_for[subject], source_path=name)
            row["epoch_id"] = f"S{subject:03d}-R{run:02d}-E{row['event_index']:03d}"
            audit.append(row)
            if row["accepted"]:
                xs.append(next(epoch_iter)); ys.append(row["label"])
                ids.append(subject); groups.append(group_for[subject]); metadata.append(row)
        print(f"Prepared {name}: {len(epochs)} accepted, {len(rows)-len(epochs)} rejected", flush=True)
    if not xs:
        raise ValueError("No usable epochs")
    x, y, subjects, splits = np.stack(xs), np.array(ys), np.array(ids), np.array(groups)
    for subject in group_for:
        if set(y[subjects == subject]) != {0, 1}:
            raise ValueError(f"S{subject:03d} has no usable observations for both classes")
    return x, y, subjects, splits, metadata, audit, files
