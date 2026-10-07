"""Regression checks for failure modes that would invalidate real EEG results."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.real_eeg.data import CHANNELS, extract_epochs, load_config
from research.real_eeg.evaluation import bootstrap_mean, evaluate, paired_comparison
from research.real_eeg.models import baseline_forward, fit_csp
from research.real_eeg.verify import verify_report

ROOT = Path(__file__).resolve().parents[1]


class RealEEGTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT/"configs/physionet-pilot.json")

    def test_subject_overlap_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["subjects"]["test"][0] = config["subjects"]["train"][0]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"config.json"; path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "overlap"):
                load_config(path)

    def test_other_run_types_cannot_be_mislabeled_as_left_right_imagery(self):
        config = copy.deepcopy(self.config); config["runs"] = [6, 10, 14]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"config.json"; path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "runs 4"):
                load_config(path)

    def test_onset_offset_resampling_class_mapping_and_qc_audit(self):
        channels = list(CHANNELS) + [f"other-{i}" for i in range(56)]
        t = np.arange(160*12)/160
        filtered = np.tile(10*np.sin(2*np.pi*10*t), (64, 1))
        annotations = [(0, 4, "T0"), (1, 4, "T1"), (5, 4, "T2"), (9, 2, "T1")]
        epochs, audit = extract_epochs(filtered, channels, annotations, self.config)
        self.assertEqual(len(epochs), 2); self.assertEqual(epochs[0].shape, (8, 256))
        self.assertEqual([r["label"] for r in audit], [0, 1, 0])
        self.assertEqual(audit[0]["epoch_start_s"], 2)
        self.assertEqual(audit[-1]["reasons"], ["annotation_too_short"])
        frequency = np.fft.rfftfreq(256, 1/128)
        self.assertEqual(frequency[np.abs(np.fft.rfft(epochs[0][0])).argmax()], 10)

    def test_overlapping_events_are_rejected_and_reported(self):
        names = list(CHANNELS) + [f"other-{i}" for i in range(56)]
        x = np.random.default_rng(42).normal(size=(64, 1600))*10
        _, audit = extract_epochs(x, names, [(0, 4, "T1"), (1, 4, "T2")], self.config)
        self.assertTrue(audit[0]["accepted"])
        self.assertIn("overlapping_event", audit[1]["reasons"])

    def test_flat_channels_do_not_disappear_from_coverage(self):
        names = list(CHANNELS) + [f"other-{i}" for i in range(56)]
        x = np.random.default_rng(42).normal(size=(64, 1600))*10; x[2] = 0
        epochs, audit = extract_epochs(x, names, [(0, 4, "T1")], self.config)
        self.assertEqual(epochs, [])
        self.assertIn("channel_std_lt_0.1_uv", audit[0]["reasons"])

    def test_uncertainty_resamples_subjects_and_paired_identical_models_are_zero(self):
        y = np.array([0, 1]*6); ids = np.repeat([1, 2, 3], 4)
        p = np.eye(2)[y]*0.8 + 0.1
        result = evaluate(y, p, ids, {"iterations": 100, "seed": 2026})
        self.assertEqual(result["subject_bootstrap_95_ci"], [1, 1])
        comparison = paired_comparison(result, result, {"iterations": 100, "seed": 2026})
        self.assertEqual(comparison["paired_subject_bootstrap_95_ci"], [0, 0])
        with self.assertRaises(ValueError): bootstrap_mean([0.5])

    def test_csp_fit_is_finite_for_rank_deficient_recordings(self):
        x = np.random.default_rng(144).normal(size=(12, 8, 256)); x[:, -1] = x[:, 0]
        filters = fit_csp(x, np.array([0, 1]*6), 4)
        self.assertEqual(filters.shape, (4, 8)); self.assertTrue(np.isfinite(filters).all())

    def test_packaged_predictions_hashes_metrics_and_split_isolation(self):
        report = verify_report(ROOT/"reports/physionet-pilot")
        self.assertEqual(report["data_kind"], "real_recorded_eeg")
        self.assertEqual(report["quality"]["raw_files"], 108)
        self.assertEqual(report["models"]["cnn_ensemble"]["subjects"], 6)

    def test_exported_baselines_replay_the_real_example(self):
        root = ROOT/"reports/physionet-pilot"
        example = json.loads((root/"example-real-window.json").read_text())
        x = np.array(example["samples"], dtype=np.float32)[None]
        with (root/"predictions.csv").open(newline="") as handle:
            row = next(r for r in csv.DictReader(handle) if r["epoch_id"] == example["provenance"]["epoch_id"])
        for name, filename in (("bandpower_logistic", "bandpower-logistic.json"), ("csp_lda", "csp-lda.json")):
            p = baseline_forward(x, json.loads((root/filename).read_text()))[0]
            expected = [float(row[f"{name}_p_left"]), float(row[f"{name}_p_right"])]
            np.testing.assert_allclose(p, expected, atol=1e-7)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "Install torch for checkpoint replay")
    def test_exported_cnn_checkpoints_replay_the_real_example(self):
        from research.real_eeg.predict import predict_window
        root = ROOT/"reports/physionet-pilot"
        example = json.loads((root/"example-real-window.json").read_text())
        probabilities = predict_window(example, root)["cnn_ensemble"]
        with (root/"predictions.csv").open(newline="") as handle:
            row = next(r for r in csv.DictReader(handle) if r["epoch_id"] == example["provenance"]["epoch_id"])
        expected = [float(row["cnn_ensemble_p_left"]), float(row["cnn_ensemble_p_right"])]
        np.testing.assert_allclose(probabilities, expected, atol=1e-6)


if __name__ == "__main__": unittest.main()
