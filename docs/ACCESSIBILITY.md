# Accessibility design and manual review

The interface is designed with large controls, keyboard alternatives and predictable pacing. This is design intent, not a WCAG conformance claim. A real-browser accessibility audit and testing with intended users remain outstanding.

| Implemented choice | Purpose |
| --- | --- |
| 88/112 px square play targets | Allow comfortable screen selection |
| Shape, label and number in addition to colour | Avoid colour-only task identification |
| Keys 1–4 plus native buttons | Provide a keyboard alternative to pointing |
| Self-paced preview and no response deadline | Let users set their own pace |
| Pause and finish-early controls | Support breaks and user agency |
| Reduced movement on by default; respects OS preference | Avoid unnecessary motion |
| Visible focus, skip link and labelled sections | Support keyboard navigation |
| Status messages and textual metrics | Provide alternatives to purely visual feedback |

The W3C [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum/) and [WCAG 2.2 specification](https://www.w3.org/TR/WCAG22/) informed these choices. Meeting one target-size criterion would not establish overall conformance.

## Before presenting a live demo

- Check Chrome/Firefox/Safari at 1440 px, 768 px and 375 px widths; add a 320 px narrow check and 200% zoom.
- Complete each activity by keyboard alone; inspect tab order and focus after scoring, pause and completion.
- Verify mouse/touch targets do not overlap; check 88 and 112 px settings.
- Check VoiceOver/NVDA reading order, cue announcements, status changes and the notebook table.
- Confirm readability and contrast in normal, increased-contrast and reduced-motion settings.
- Export JSON/CSV, open the files, and reload the app to confirm its in-memory data lifetime.
- Background the browser mid-response, return and confirm an explicit resume is required.

Waveforms have a textual overview and quality/power summaries but no full nonvisual sample explorer. Single-switch scanning, custom key mapping, localisation, full screen-reader chart navigation and physical input devices are future work. Timings combine recall, choice and interaction; they are not calibrated motor measurements.


## Version 2 browser check

Headless Chromium 154.0.8037.92 rendered the standalone page at 1440 × 1000
and 390 × 844 CSS pixels. Recorded/synthetic switching worked, three real
model results appeared, and neither width produced document-level horizontal
overflow. No script errors or runtime network requests were observed. The
screenshots are actual browser renderings. These checks do not substitute for
physical touch, screen readers, keyboard navigation across all controls or a
full WCAG audit.
