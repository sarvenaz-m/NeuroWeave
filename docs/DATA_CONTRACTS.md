# Data contracts

## EEG windows

The sample file is [example-window.json](../data/example-window.json). Import accepts JSON under 500,000 bytes, with the following contract. Unknown fields are discarded.

| Field | Required value |
| --- | --- |
| `schema` | `neuroweave.eeg.v1` |
| `sample_rate_hz` | 128 |
| `unit` | `uV` |
| `channels` | Eight unique strings, each at most 24 characters |
| `samples` | Eight arrays of exactly 256 finite numbers; absolute value ≤ 100000 |
| `source` | Exported provenance; imports are forced to `user-supplied` |

There is no resampling, channel selection or montage mapping. Inputs in volts/millivolts must be correctly converted to µV by the producer; a misleading unit label cannot be detected. Signal quality and scientific suitability are separate from schema validation. Classification is disabled for every import.

## Session export

`neuroweave.session.v1` records local behaviour. `clinical_validation` is always false. The top-level fields include app version, mode, seed, planned rounds, current state, settings, records, events and summary.

| Record field | Meaning |
| --- | --- |
| `round` | One-based completed round |
| `mode` | `memory` or `switch` |
| `level` | Configured memory length, including in switch mode where the actual expected sequence length is always one |
| `rule` | `match` / `opposite` for switch; null for memory |
| `expected` | Zero-based shape IDs: Node 0, Pulse 1, Phase 2, Gate 3 |
| `responses` | Shape value, active-time offset in ms and input method for each selection |
| `correct` | Exact match of the entire response sequence |
| `duration_ms` | Ready-to-final-response time excluding pauses |
| `paused_ms` | Total pause time within the response phase |
| `layout` | End-of-round viewport and target rectangles in CSS pixels; DOM-only environment may report zero geometry |

The CSV is a compact round-level projection and excludes geometry, individual selections and signal observations. The ledger’s displayed “Buffer” is actual expected sequence length, while CSV `level` retains the setting described above.

`signal_observations` stores up to 200 independent window observations in a session. It includes time, source, quality result and optional synthetic classification. It does not contain raw imported signals and is not synchronous acquisition. Window export is a separate user action. Metrics combine rounds across any explicitly accepted level changes; the per-round log is necessary for condition-specific comparisons.

Session files are exports, not an implemented session-import API. Imported EEG JSON follows the separate contract above.

## Stimulus identity in version 1.1

Symbol IDs remain 0–3 with pairs 0↔2 and 1↔3. Version 1.1 uses **Node, Pulse, Phase, Gate** and exports their names in the top-level `symbols` array. Version 1.0 used Leaf, Sun, Wave, Moon. Use `app_version` and `symbols` to interpret exports; the redesigned stimuli are not interchangeable conditions for a human performance comparison. UI “trial” corresponds to the serialized `round` field.
