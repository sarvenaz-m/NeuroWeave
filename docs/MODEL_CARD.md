# Model card / version 2

## Recorded EEG: CompactEEGCNN

| Field | Value |
| --- | --- |
| Task | Offline left/right fist motor-imagery classification |
| Input | Preprocessed 8 × 256 microvolt epoch at 128 Hz |
| CNN | Independent PyTorch implementation of an EEGNet-style temporal/depthwise/separable design |
| Trainable parameters | 1,490 per checkpoint |
| Training people | 24 from the fixed 36-person pilot cohort |
| Selection | Minimum validation loss on 6 different people, independently for 3 seeds |
| Primary predictor | Mean probability of seeds 144, 2026 and 42 |
| Test people | 6 unseen participants, no subject calibration or test tuning |
| Outputs | Cue-class softmax scores; uncalibrated |

### Architecture

Input `[batch,1,8,256]` → 8 temporal filters of width 64 with explicit same
padding → BatchNorm → grouped spatial convolution across all 8 channels,
depth multiplier 2 → BatchNorm / ELU → average pool 4 / dropout 0.5 →
16 depthwise temporal filters of width 16 → 16 pointwise filters → BatchNorm /
ELU → average pool 8 / dropout → flatten 128 → two logits.

Trainable count: 512 temporal weights + 128 spatial weights + 256 depthwise
weights + 256 pointwise weights + 80 BatchNorm scalars + 258 classifier
scalars = **1,490**. Running BatchNorm statistics are additional non-trainable
state. Spatial filter norms are capped at 1; each classifier row at 0.25.

The design is based on [EEGNet](https://arxiv.org/abs/1611.08024). This is a
small implementation for this project's preprocessing and split; its results
are not a reproduction of the paper's datasets or evaluation protocol.

### Training and reference models

Fit channel normalization and class weights on training people only.
AdamW, learning rate 0.001, weight decay 0.0001, batch 64, maximum 80 epochs,
early-stopping patience 20. Validation loss selects each checkpoint. Test data
is never used for fitting BatchNorm, scaling, CSP, model selection or thresholds.

References are Welch log-band-power + training-scaled balanced logistic
regression, and regularized CSP + automatic shrinkage LDA. Validation chooses
logistic C and the CSP component count. See [the protocol](REAL_EEG_PROTOCOL.md)
for the exact grid, covariance estimator and bands.

### Evidence and limits

The [real report](../reports/physionet-pilot/benchmark.json) contains actual
scores, participant-bootstrap intervals, per-person results, paired
comparisons, and each seed's selected epoch and learning curves. The
[prediction table](../reports/physionet-pilot/predictions.csv) allows metric
recalculation. Exported models are replayed against the recorded sample.

This is one convenience cohort and one fixed subject split. Six test people
limit precision; initialization seeds do not add independent participants.
Filtered accepted epochs omit some artifacts, with coverage reported.
The filtering is offline/acausal; there is no real-time performance claim.
Softmax is uncalibrated and the study contains no human usability evaluation.

Browser replay of recorded/imported EEG never invokes the synthetic decoder.
The real CNN runs through the Python pipeline. An input file declaring the
correct shape and preprocessing does not independently authenticate its origin.

---

# Synthetic TinyTemporalCNN reference

| Field | Value |
| --- | --- |
| Version | 1.0.0, September 2026 |
| Intended use | Inspectable artificial-signal classification in a reproducible research prototype |
| Input | 8 channels × 256 samples, 128 Hz, microvolts |
| Labels | Artificial Condition A and Condition B |
| Parameters | 1,114 trainable scalars |
| Training implementation | NumPy; explicit convolution, gradients and Adam |
| Browser implementation | JavaScript forward pass using the exported weights |
| Clinical validation | None |

## Architecture and preprocessing

Subtract each channel’s mean within each window, then divide by a fixed 20 µV. No dataset-level scaling is fitted, and held-out statistics are not used. This removes the DC component but is not a band-pass filter or a complete EEG preprocessing pipeline. No ICA, re-referencing, electrode montage or line-noise removal is implemented.

Input `[8,256]` → valid temporal convolution `[8 filters,8 inputs,17 samples]` at stride 4 → `[8,60]` → ReLU → global temporal mean `[8]` → linear head `[2]` → softmax.

Parameter count: 8 × 8 × 17 + 8 + 8 × 2 + 2 = 1,114. The operation is cross-correlation, following common neural-network convolution convention. It is a small custom architecture, not an EEGNet implementation. Softmax output is uncalibrated and is not a probability of a clinical condition.

## Training and evaluation

Generator seed 144; training-shuffle seed 2026; 24 epochs; batch size 32; Adam with learning rate 0.003, beta1 0.9, beta2 0.999 and epsilon 1e-8. Select the checkpoint with the lowest validation cross-entropy. The supplied run selects epoch 24.

Split by virtual subject before fitting: 12 training, 3 validation and 3 test virtual subjects. The fixed split is transparent but is not cross-validation. No threshold or checkpoint is chosen using test results. Results are reported for one seed; this is not evidence of statistical robustness.

The baseline computes log(beta power / alpha power), then chooses the nearest of two training-class mean features. Alpha is `[8,13)` Hz and beta is `[13,30]` Hz. The PSD is a one-sided Hann periodogram, scaled in µV²/Hz and averaged across channels; band integration sums bins times Δf = 0.5 Hz.

Both models classify 96/96 held-out artificial windows correctly. This does not demonstrate superiority of deep learning. Frequency labels are deliberately easy to separate. The report contains a confusion matrix, learning history, per-virtual-subject results and a dataset hash.

## Quality and inference boundaries

Windows must have the exact shape and finite samples. A channel standard deviation below 0.5 µV or any absolute sample over 150 µV makes the demo abstain. Thresholds are illustrative engineering defaults, not validated acquisition criteria. Other artefacts, such as motion, line noise, clipping below the amplitude threshold or systematic drift, may pass.

Only internally generated synthetic windows are classified in the UI. Imported data is always re-labelled `user-supplied` and has classification disabled, regardless of its declared source. Spectral analysis remains available. Imported data is never uploaded by this app.

## Numerical verification

Four test-subject fixtures check Python-to-JavaScript softmax agreement within 1e-10 and PSD agreement within 1e-8. Python tests verify finite-difference parameter gradients, correct spectral energy and the packaged held-out accuracy. Tolerances test this implementation, not clinical correctness.

## Out-of-scope uses

This synthetic-only model is not used for real EEG or motor-imagery inference. Attention estimation, diagnosis, treatment decisions, rehabilitation claims and automated neurofeedback remain outside the project scope. The real EEG experiment above uses a separately trained model and public recordings.
