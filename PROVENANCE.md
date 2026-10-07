# Provenance and evidence

NeuroWeave implements EEG analysis, model evaluation and cognitive task
interaction as an independent portfolio research project. Version 2 extends
the original synthetic reference with a newly executed public-data experiment.

## Recorded data and results

The real experiment uses PhysioNet EEGMMIDB version 1.0.0, contributed by
Gerwin Schalk and the Wadsworth Center BCI R&D Program. It uses subjects
S001–S036 and unilateral fist-imagery runs 04/08/12, with source SHA-256 hashes
verified against the official index. See [data attribution](LICENSE_DATA.md)
and [the protocol](docs/REAL_EEG_PROTOCOL.md).

The packaged run contains 1,620 recorded trials, with 24/6/6 separate people
for train/validation/test. It ran on CPU and exports actual predictions,
checkpoints, learning histories, QC decisions, environment versions and hashes.
The single waveform example is a processed training-cohort public trial;
its trace is not an illustration or a test-accuracy measurement.

The PyTorch CNN independently implements an EEGNet-style temporal/depthwise/
separable design. The architecture source is cited; neither published EEGNet
performance nor the original thesis experiments are claimed as these results.

## Synthetic reference and browser trust

The older NumPy benchmark, tiny CNN weights and generic-channel example are
artificial frequency-condition data. Their perfect accuracy demonstrates an
easy synthetic task. They remain separate from real EEG results.

The browser classifies only internally generated synthetic windows. All imports
are user-supplied, and recorded replay has analysis without synthetic inference.
A declared source in a file is not proof of origin. Task responses and signal
observations are independent records; the app does not acquire synchronized
EEG while a person plays.

## Interface and artwork

Response symbols and SVG illustrations are original code-native graphics.
Existing cover/system illustrations are not screenshots or acquired signals.
The new scientific figures are drawn directly from verified numerical results
and recorded sample values. Code and original artwork use [MIT](LICENSE).

Software checks cover numerical correctness, split isolation, artifact
integrity, saved-model replay and task transitions. The EEG experiment evaluates
an offline public dataset. Human usability, hardware acquisition and clinical
outcomes have not been evaluated. Historical MSc context describes the author's
research background, separately from this new experiment.
