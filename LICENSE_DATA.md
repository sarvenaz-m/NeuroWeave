# Public EEG data attribution

NeuroWeave source code and original artwork are covered by [MIT](LICENSE).
PhysioNet EEGMMIDB recordings, the processed real EEG example, and the derived
trial-level benchmark tables are attributed separately under the
[Open Data Commons Attribution License 1.0](https://physionet.org/content/eegmmidb/view-license/1.0.0/).

**Source:** Gerwin Schalk. *EEG Motor Movement/Imagery Dataset*, version 1.0.0
(2009). PhysioNet. DOI: [10.13026/C28G6P](https://doi.org/10.13026/C28G6P).

The recordings were created by the BCI R&D Program at the Wadsworth Center,
New York State Department of Health. NeuroWeave downloads selected EDF files
from the official public archive and verifies the published SHA-256 values.
The raw archive is excluded from this repository. The included EEG window is
a processed derivative; its file identifies the subject/run/event, units,
channel selection and preprocessing. The dataset remains a separate work
from the project's MIT-licensed implementation.

When reusing the data or derived tables, retain this attribution and link to
the dataset and its license. Cite the original BCI2000 publication:

Schalk, G., McFarland, D. J., Hinterberger, T., Birbaumer, N., and Wolpaw, J. R.
*BCI2000: a general-purpose brain-computer interface (BCI) system.* IEEE
Transactions on Biomedical Engineering, 51(6), 1034–1043 (2004).
[DOI: 10.1109/TBME.2004.827072](https://doi.org/10.1109/TBME.2004.827072).

Also cite the PhysioNet platform as requested by the dataset provider; current
citation guidance is on the [dataset page](https://physionet.org/content/eegmmidb/1.0.0/).
