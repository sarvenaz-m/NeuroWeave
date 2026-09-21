# Validation record

Build reviewed: **1.1.0 · 21 September 2026**.

| Check | Result | Practical boundary |
| --- | --- | --- |
| JavaScript signal and engine tests | 15 passed | Deterministic functions and timing logic |
| DOM integration tests | 6 passed | jsdom; does not render pixels or emulate physical touch |
| Python research tests | 6 passed | Numerical correctness, split integrity, saved-model evaluation |
| Standalone build | Passed | HTML, CSS, model and script bundled without runtime network dependencies |
| Local documentation links | Checked | Local targets only; not proof of future external availability |
| Original cover, lattice, system map, palette and research figures | Rendered and visually inspected | Illustrations and exact plots; not UI screenshots |
| Real-browser visual/touch/accessibility testing | Not performed | Complete the manual checklist before presentation |
| User study or clinical validation | Not performed | Study protocol is proposed |

## Checks that matter

The signal tests compare the JavaScript CNN with independent Python outputs on four held-out virtual-subject windows. PSD values are compared with NumPy FFT results; a known 10 Hz sine checks peak position and integrated power. Python tests check analytic gradients against finite differences, exclude subject overlap across splits and recompute held-out accuracy from exported weights.

Game tests verify pause subtraction, preview timing, invalid time rejection, duplicate/out-of-phase input handling, explicit difficulty acceptance, deterministic rule switching and early termination. DOM tests exercise cue hiding, keyboard responses, notebook rows, pause/resume, artefact abstention and imported-data classification blocking.

Responsive CSS, physical touch and assistive technologies require the [manual checklist](docs/ACCESSIBILITY.md). DOM tests verify events and state; they do not render browser pixels.

## Run the same checks

```bash
npm ci --ignore-scripts
npm run check
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
```

Training ran successfully and produced the weights and report shipped here. The artificial benchmark score is not a software test count and not a clinical outcome. Floating-point details may vary across platforms; reference checks use explicit tolerances.

## Version 1.1 scope

The identity redesign changes presentation, labels and visible stimuli. Existing interaction checks are rerun against the rebuilt demo. The numerical model is unchanged; the six Python tests verify its calculations and packaged weights. No new human-performance comparison between the old and new symbols has been performed.

The five primary text/background palette pairs were checked numerically: the lowest contrast ratio was 5.26:1. This limited palette check is not a full accessibility audit. The standalone build also passed resource-embedding, duplicate-ID, anchor and module-order checks.
