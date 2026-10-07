# Sources and technical references

## Recorded EEG data

- Schalk, G. (2009), [EEG Motor Movement/Imagery Dataset v1.0.0](https://physionet.org/content/eegmmidb/1.0.0/), DOI [10.13026/C28G6P](https://doi.org/10.13026/C28G6P). Data provider and event meanings.
- Schalk et al. (2004), [BCI2000](https://doi.org/10.1109/TBME.2004.827072). Original acquisition-system publication.
- [MNE EEGBCI run mapping](https://mne.tools/stable/generated/mne.datasets.eegbci.load_data.html), identifying unilateral imagery runs 4/8/12. The executed pipeline pins MNE 1.11.0.
- [Dataset attribution and license](../LICENSE_DATA.md).

## Related EEG research

- Lawhern, V. J. et al., [EEGNet: A Compact Convolutional Network for EEG-based Brain–Computer Interfaces](https://arxiv.org/abs/1611.08024). Architecture source for the v2 temporal/depthwise/separable CNN. Its independent PyTorch implementation uses this project's input shape, preprocessing and evaluation split; it does not reproduce the paper's experiments. The older NumPy model is a separate, simpler synthetic reference.

## Implementation and interaction design

- [NumPy sliding_window_view](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html): overlapping array-window primitive used to form temporal convolution patches.
- [SciPy signal-processing source](https://github.com/scipy/scipy/blob/main/scipy/signal/_spectral_py.py): reference for standard periodogram density scaling; runtime analysis here uses its own NumPy/JavaScript implementation.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum/): interaction-design references. No full conformance claim is made.

References document data, architecture and implementation context. The project's own evidence is in the recorded benchmark and validation report.
