# Synthetic dataset card

This repository contains no participant EEG dataset. `research/neuro.py` generates artificial two-second windows that exercise the signal-analysis and machine-learning pipeline.

| Property | Definition |
| --- | --- |
| Generator | NumPy random generator; seed 144 |
| Scale | 18 virtual subjects × 32 windows = 576 |
| Sampling | 128 Hz, 256 samples, 8 generic channels |
| Conditions | Alternating A/B labels, 16 of each per virtual subject |
| Dominant component | A ≈ 10 Hz; B ≈ 20 Hz, with small frequency jitter |
| Nuisance terms | Channel gains, phases, offsets, slow drift, additive noise and a weaker opposite-frequency component |
| Labels | Generator conditions; no psychological, motor or clinical interpretation |
| Distribution rights | Newly generated arrays; MIT project licence |

`virtual-01` is a simulation identifier, not a participant ID. Generic channel labels C1–C8 are placeholders and do not define a 10–20 montage. The generator does not model neurophysiology, electrode contact, realistic artefact distributions or interactions among real people.

The browser uses a separate deterministic demonstration generator with similar artificial frequency components. Its xorshift generator is not the NumPy benchmark generator. Browser windows are not the held-out benchmark and no browser-wide model accuracy claim is made. Numeric parity fixtures use the exact Python-generated arrays.

The example JSON is an artificial window from virtual subject 16. Importing it demonstrates the data contract, not a real acquisition pathway. In the UI all imports disable classification.

Do not place personal recordings in this public repository. A `private-data/` directory is ignored by Git as a convenience, not an access-control mechanism.
