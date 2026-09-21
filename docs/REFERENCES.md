# Sources and technical references

## Related EEG research

- Lawhern, V. J. et al., [EEGNet: A Compact Convolutional Network for EEG-based Brain–Computer Interfaces](https://arxiv.org/abs/1611.08024). Related work on compact EEG convolutional models. NeuroWeave’s simpler CNN is newly implemented and is not EEGNet, a reproduction of its experiments or a model trained on its datasets.

## Implementation and interaction design

- [NumPy sliding_window_view](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html): overlapping array-window primitive used to form temporal convolution patches.
- [SciPy signal-processing source](https://github.com/scipy/scipy/blob/main/scipy/signal/_spectral_py.py): reference for standard periodogram density scaling; runtime analysis here uses its own NumPy/JavaScript implementation.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum/): interaction-design references. No full conformance claim is made.

References explain the basis and implementation context; they do not validate the synthetic model or confer institutional endorsement.
