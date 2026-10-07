# PhysioNet pilot / executed version 2 benchmark

Real recorded EEG, 36 public participants, motor-imagery runs 4/8/12.
The fixed subject split was declared before fitting. 1,620 epochs passed the
fixed QC policy; 270 are from six test participants.

| Predictor | Participant mean balanced accuracy | 95% participant bootstrap interval |
| --- | --- | --- |
| Band power + logistic | 59.30% | 47.70–72.85% |
| CSP + LDA | 54.90% | 49.60–60.59% |
| CNN / three-seed ensemble | 63.65% | 53.71–77.10% |

Primary scores average participant-level balanced accuracy; pooled trial
balanced accuracy is also recorded and differs slightly. Intervals resample
participants, not trials. The paired CNN–band-power interval includes zero.

Artifacts:

- `benchmark.json`: metrics, histories, selected epochs, versions and hashes.
- `predictions.csv`: every accepted trial, split, cue label and class probabilities.
- `epoch-audit.csv`: every candidate trial and its acceptance/rejection reasons.
- `source-manifest.json`: official EDF URLs, hashes, sizes and QC counts.
- `config.json`: exact subject lists and settings.
- `cnn-seed-*.pt`: tensor state dictionaries, loaded with `weights_only=True`.
- `cnn-normalization.json`: training-fitted statistics and input contract.
- `bandpower-logistic.json`, `csp-lda.json`: frozen reference parameters.
- `example-real-window.json`: attributed, processed public training-cohort trial.

Use the commands in the [main README](../../README.md) to verify artifacts or
retrain from independently downloaded source data. See [data licensing](../../LICENSE_DATA.md)
and the [protocol](../../docs/REAL_EEG_PROTOCOL.md).

The complete 109-person experiment has not been executed. The six-person test
cohort and a single split limit generalization; model output is uncalibrated.


## Variation and errors

| Test participant | Band power | CSP + LDA | CNN ensemble |
| --- | --- | --- | --- |
| S005 | 39.3% | 50.0% | 53.9% |
| S008 | 66.1% | 59.3% | 62.5% |
| S009 | 45.8% | 51.5% | 54.8% |
| S027 | 56.1% | 44.8% | 49.1% |
| S029 | 91.3% | 58.7% | 95.7% |
| S032 | 57.1% | 65.2% | 66.1% |

The CNN ensemble correctly classified 79/134 left cues and
92/136 right cues. Participant performance varies markedly;
S029 is especially easy for the CNN and band-power reference in this split.
Scores near chance on other people remain visible, without excluding them
after viewing the test results.

Individual CNN seed participant-mean scores: 144: 56.39%, 2026: 52.00%, 42: 59.82%.
The ensemble is the predeclared predictor; no test-based seed selection was used.
