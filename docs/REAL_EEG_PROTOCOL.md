# Recorded EEG evaluation protocol

## Question and cohort

Can a compact CNN and two conventional references distinguish left/right fist
imagery in people whose EEG was not used for training? This is a fixed-split,
offline motor-imagery benchmark.

The source is [PhysioNet EEGMMIDB v1.0.0](https://physionet.org/content/eegmmidb/1.0.0/),
DOI [10.13026/C28G6P](https://doi.org/10.13026/C28G6P). The pilot takes numbered
subjects S001–S036 to keep download and CPU costs manageable. This convenience
subset is not a random sample of the full population. A NumPy permutation with
seed 2026 fixed the subject groups before training. Exact identifiers are in
[the config](../configs/physionet-pilot.json); 24 people train, 6 validate and 6 test.

## Event interpretation

Use only runs **4, 8, 12**, the three repetitions of unilateral fist **imagery**.
For those runs, `T1` is imagined left fist and `T2` is imagined right fist.
`T0` rest is omitted. Runs 3/7/11 are actual movement; runs 6/10/14 use different
imagery labels (both fists/both feet). The adapter rejects a different run set.

For each T1/T2 event, extract exactly **[onset+1, onset+3)** seconds. Require the
annotation to last at least 3 seconds and the epoch to lie in the recording.
Each cue contributes at most one epoch. Overlapping event windows are rejected.
There is no sliding-window augmentation. All epochs from a person stay together.

## Preprocessing and quality

1. Verify every EDF against the official SHA-256 index. The index itself is
   pinned to SHA-256 `7f5d16957d8ee7bce86cc7ccba0e5994f63f33781607eb3f838392d49311a208`.
2. Read EDF+ with MNE, normalize channel names, require 64 EEG channels and
   160 Hz. MNE returns volts; multiply by `1e6` to use microvolts throughout.
3. Subtract the instantaneous average across all 64 channels. Apply a
   fourth-order Butterworth 1–40 Hz bandpass to each full run with SciPy
   `sosfiltfilt`. This is offline, zero-phase filtering; future samples within
   the recording are used. Nothing is filtered across different subjects.
4. Select FC3, FC4, C3, Cz, C4, CP3, CPz, CP4 in that order. Extract the event
   window, use `resample_poly(up=4, down=5)` with its default antialias filter
   and zero-padding, then subtract each epoch/channel's temporal mean.
5. Reject an epoch if any selected channel has peak-to-peak amplitude above
   500 µV or standard deviation below 0.1 µV. Shape must be 8 × 256 and finite.

QC settings are fixed engineering choices. Every considered event, including
rejection reasons, is exported in `epoch-audit.csv`. Accepted/rejected counts
are reported by file and split. Subjects without usable examples of both
classes cause an explicit error; no subject is silently omitted. Scores apply
to accepted epochs, so reported coverage must accompany the scores.

## Fit and model selection

| Model | Training data only | Validation selection |
| --- | --- | --- |
| Band power + logistic | Welch PSD (128-sample Hann segments, 64 overlap), log powers in [8,12), [12,20), [20,30) Hz; StandardScaler; balanced logistic regression | C in 0.01, 0.1, 1, 10, maximizing subject-mean balanced accuracy |
| CSP + LDA | Trace-normalized epoch covariance, class covariance shrinkage 0.1, CSP spatial filters; log normalized variance; automatic shrinkage LDA | 2, 4, 6 CSP components, maximizing subject-mean balanced accuracy |
| Compact CNN | Training-fitted channel mean/std; class weights from train; AdamW updates and BatchNorm statistics on train only | Minimum unweighted validation cross-entropy, separately for each seed |

Ties in baseline selection retain the earliest candidate (stronger
regularization/fewer CSP components). Validation is not added to training after
selection. Test signals use frozen training statistics.

The CNN uses seeds 144, 2026 and 42, at most 80 epochs, patience 20, batch size
64, learning rate 0.001, weight decay 0.0001 and dropout 0.5. CPU execution uses
two PyTorch threads and deterministic algorithms. Convolution and dense weight
norms are constrained after each update. The primary CNN equally averages the
three selected checkpoints' softmax probabilities; the best seed is not chosen
using test scores. Individual seed results and full learning curves are exported.

## Test metrics and uncertainty

The **primary metric** is the unweighted mean of each test subject's balanced
accuracy. Also report pooled accuracy, balanced accuracy, macro F1, ROC AUC,
confusion matrices, per-subject scores and counts. Use probability argmax;
exact ties resolve to the left class. Softmax scores are not calibrated.

Intervals use 5,000 bootstrap draws with seed 2026, resampling the six test
people with replacement and taking the 2.5th/97.5th percentiles of the mean
score. Paired differences use the same per-person CNN-minus-baseline
differences. These exploratory intervals do not address split-selection
uncertainty or establish superiority from one small cohort.

## Artifacts and reproduction

`benchmark.json` records metrics, config, software versions, checkpoint
selection, training time, code hashes and output hashes. `source-manifest.json`
records official URLs, raw EDF hashes, sizes and QC counts. `predictions.csv`
contains class probabilities and cue labels for every accepted trial.
Plain-JSON baseline parameters and PyTorch state dictionaries enable replay.

`verify.py` checks hashes, split membership, QC consistency and recomputes
primary and individual-seed results from predictions. This is an artifact
consistency check; downloading verified raw files and retraining is the
stronger reproduction step. `predict.py` reloads all saved models for the
attributed example. The raw EDF cache is git-ignored.

The full 109-subject configuration is a separate, unexecuted protocol. It can
stop on source anomalies. Any eligibility change needs a new documented config
and a new result directory; retain the pilot's original cohort and results.
