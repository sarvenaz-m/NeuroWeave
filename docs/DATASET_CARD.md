# Dataset card / version 2

## Recorded EEG

| Property | Definition |
| --- | --- |
| Provider | PhysioNet; EEG Motor Movement/Imagery Dataset, Gerwin Schalk |
| Version / DOI | 1.0.0 / [10.13026/C28G6P](https://doi.org/10.13026/C28G6P) |
| Original collection | 109 participants, 64 channels, 160 Hz, EDF+ |
| Packaged pilot | S001–S036, runs 4/8/12 only; 108 verified raw files |
| Labels | T1 left-fist imagery; T2 right-fist imagery; rest omitted |
| Epoch | One [onset+1, onset+3) second window per cue |
| Motor channels | FC3, FC4, C3, Cz, C4, CP3, CPz, CP4 |
| Processing | 64-channel common average, 1–40 Hz offline bandpass, resample 160→128 Hz, epoch mean removal |
| QC | Reject >500 µV channel peak-to-peak or <0.1 µV channel standard deviation |
| Split | 24 train / 6 validation / 6 test people, fixed before training |
| License | ODC-By-1.0; see [data attribution](../LICENSE_DATA.md) |

The source contains movement and imagery tasks with different meanings for
T1/T2. Only unilateral imagery runs are eligible. A convenience subset limits
population coverage; the pilot does not evaluate all 109 subjects. No
participant demographics, names or inferred health labels are introduced.

Raw EDF files are downloaded on demand and git-ignored. The repository ships
one attributed processed trial, source hashes, trial labels/probabilities and
QC records. Counts after QC are in the [recorded benchmark](../reports/physionet-pilot/benchmark.json).
Rejected trials remain visible in its [audit](../reports/physionet-pilot/epoch-audit.csv).

Read the [complete preprocessing and evaluation protocol](REAL_EEG_PROTOCOL.md).
The acausal filter supports offline analysis, not latency-sensitive streaming.
The browser's synthetic quality gate has different thresholds from the real
benchmark's QC policy. Replay/import in the browser provides analysis only.

---

# Synthetic reference dataset

`research/neuro.py` retains the original artificial two-second reference windows separately from the recorded EEG benchmark.

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
