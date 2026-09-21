# TinyTemporalCNN model card

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

Real EEG decoding, motor-imagery BCI, attention estimation, diagnosis, treatment decisions, clinical rehabilitation claims and automated neurofeedback are out of scope. No EEG acquisition hardware, real participants or original thesis datasets were used. To investigate a real-data question, establish the target task, rights to use the data, montage/preprocessing, participant-level split strategy, artefact handling and appropriate validation before training a new model.
