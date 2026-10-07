"""Re-evaluate exported models on the packaged, attributed real EEG window."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .data import CHANNELS
from .models import baseline_forward, cnn_forward, make_cnn
from .verify import verify_report


def predict_window(window, root):
    root = Path(root)
    report = verify_report(root)
    pp = report["preprocessing"]
    if (window.get("source") != "physionet-eegmmidb" or window.get("sampling_rate_hz") != 128
            or window.get("units") != "microvolts" or window.get("channels") != list(CHANNELS)
            or window.get("preprocessing") != pp):
        raise ValueError("Window must declare the v2 PhysioNet preprocessing and channel contract")
    x = np.array(window["samples"], dtype=np.float32)[None]
    if x.shape != (1, 8, 256) or not np.isfinite(x).all():
        raise ValueError("Expected finite [8, 256] window")
    if np.any(np.ptp(x, axis=-1) > pp["max_peak_to_peak_uv"]) or np.any(x.std(axis=-1) < pp["min_channel_std_uv"]):
        raise ValueError("Window fails the real EEG quality policy")
    result = {}
    for name, filename in (("bandpower_logistic", "bandpower-logistic.json"), ("csp_lda", "csp-lda.json")):
        result[name] = baseline_forward(x, json.loads((root/filename).read_text()))[0].tolist()
    import torch
    torch.set_num_threads(2)
    norm = json.loads((root/"cnn-normalization.json").read_text())
    mean, scale = np.array(norm["mean"], dtype=np.float32), np.array(norm["scale"], dtype=np.float32)
    probabilities = []
    for run in report["cnn_runs"]:
        model = make_cnn(norm["dropout"])
        model.load_state_dict(torch.load(root/run["checkpoint"], map_location="cpu", weights_only=True))
        probabilities.append(cnn_forward(model, x, mean, scale)[0])
    result["cnn_ensemble"] = np.mean(probabilities, axis=0).tolist()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default="reports/physionet-pilot")
    parser.add_argument("--window")
    args = parser.parse_args()
    root = Path(args.report_dir)
    window = json.loads(Path(args.window or root/"example-real-window.json").read_text())
    result = predict_window(window, root)
    print(json.dumps({"classes": ["left_fist_imagery", "right_fist_imagery"], "probabilities": result,
                      "note": "Research predictions; input provenance is declared, not independently authenticated"}, indent=2))


if __name__ == "__main__":
    main()
