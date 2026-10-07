# Validation record

Build: **2.0.0 · 3 October 2026**.

| Check | Result | Scope |
| --- | --- | --- |
| JavaScript core | 15 passed | Signal math, synthetic Python/JS parity and task state/timing |
| DOM integration | 9 passed | Recorded/synthetic trust boundaries, imports, evidence table and task controls |
| Python synthetic research | 6 passed | Analytic gradients, spectral energy and original saved model |
| Python recorded EEG | 10 passed | Subject/run isolation, epoch timing/resampling, QC audit, CSP rank stability, uncertainty and model replay |
| Total automated tests | **40 passed; 0 failed; 0 skipped** | Current local execution; GitHub will rerun after push |
| Real data execution | Completed on CPU | 108 official-hash-verified EDF files, 36 participants, 1,620 accepted cues |
| Held-out evaluation | Completed | 270 trials from 6 people absent from training and validation |
| Artifact verification | Passed | Hashes, split membership, counts, primary/seed metrics and participant intervals |
| Exported model replay | Passed | Plain-JSON references and all three PyTorch checkpoints reproduce saved example probabilities |
| Standalone build | Passed | Embedded resources; no application runtime network dependencies |
| Chromium rendering / smoke | Passed | 1440 × 1000 and 390 × 844; no script errors or horizontal overflow |
| Physical touch / screen reader / human study | Not performed | See the remaining accessibility and study checklists |

The [machine-readable record](reports/validation.json) separates software
checks, recorded-data execution and browser rendering. [Browser evidence](reports/browser-smoke.json)
records the engine version, states, viewport widths, script errors and network requests.
Screenshots in `docs/media/console-*.png` are actual headless Chromium renderings.
The cover and lattice remain illustrative vector art.

## Recorded EEG evidence

The fixed pilot uses 24 training, 6 validation and 6 test people. Preprocessing
and subject membership were declared before fitting. All 1,620 candidate
windows passed the specified conservative QC policy; the audit records that
zero rejections occurred, rather than claiming broader artifact removal.
The packaged CPU run took about 86 seconds excluding download/install time.

Primary subject-mean balanced accuracy: CNN ensemble **63.65%**, band-power
logistic **59.30%**, CSP + LDA **54.90%**. The paired CNN–band-power 95% interval
includes zero. Results describe this cohort/split and accepted offline epochs;
three CNN seeds are not three independent participant samples.

Verification recalculates metrics from saved trial predictions. Saved-model
replay also checks inference against the recorded example. To independently
reproduce acquisition, preprocessing and fitting, download the verified EDFs
and rerun the [training commands](README.md#reproduce-training-on-the-real-recordings).
The final release run also reproduced the earlier trial probabilities and metrics
exactly on the same CPU/software environment. The complete 109-person
experiment has not been executed.

## Run the checks

```bash
npm ci --ignore-scripts
npm run check
python -m pip install -r requirements-real.txt
python -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
python -m unittest discover -s tests -p 'test_*.py' -v
python -m research.real_eeg.verify --check-code
python -m research.real_eeg.predict
```

CI runs the build, JavaScript/DOM checks, Python checks and report verification
without downloading participant recordings. The published v1 CI success is
historical; a v2 GitHub Actions run only exists after these changes are pushed.

## Browser and manual boundaries

Headless Chromium 154.0.8037.92 successfully loaded the offline file, showed
recorded EEG and three real scores, switched to synthetic predictions and
returned to recorded analysis without classification. Network monitoring
observed no runtime requests beyond the local document. Both viewport widths
had no document-level horizontal overflow; mobile tables scroll within their
container. The rendered signal and evidence panels were visually inspected.

Physical-device input, assistive technology, synchronized hardware acquisition
and usability outcomes were not evaluated. Follow [accessibility](docs/ACCESSIBILITY.md)
and the [proposed study protocol](docs/STUDY_PROTOCOL.md) for those next steps.
