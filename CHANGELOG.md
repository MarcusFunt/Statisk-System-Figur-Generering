# Changelog

## [0.3.0] - 2026-09-01

### Fixed
- Preserved insertion order by default and added explicit `z_index` layering.
- Replaced flat SVG regrouping with one semantic group per logical element and optional ID namespaces.
- Preserved isotropic SVG geometry when both output dimensions are specified.
- Corrected transparent/non-white hinge and roller handling, including beam knockout around hinges.
- Centered fixed-support walls so hatch roots remain attached.
- Added finite-number, geometry, enum-like, and style validation.
- Restored `pixels_per_unit` to true pixels/viewBox-units per drawing unit semantics.
- Prevented Matplotlib `ax=` rendering from mutating the parent figure background.
- Scaled SVG dash patterns in the same physical units as stroke widths.
- Escaped SVG style-derived attribute values.
- Made multiline and literal `$...$` text behavior consistent between renderers.
- Clamped arrowheads for very short arrows.

### Added
- Ordered semantic element model, explicit layers, sub-diagram transforms, and per-element styling/classes.
- Higher-fidelity text metrics with a dependency-free fallback and scored label placement.
- Physical-output-aware symbol sizing and automatic distributed-load spacing.
- Triangular/trapezoidal loads, standalone springs, links, guided/sliding supports, curved members, axes, section markers, angle dimensions, leaders, and displacement symbols.
- Dimension witness lines and configurable endpoint styles.
- Dependency-free SVG installation; Matplotlib is now an optional extra.
- Scene-level visual regression tests, edge-case tests, minimum-Matplotlib CI, static typing CI, and wheel/sdist smoke tests.

## [0.2.0] - 2026-09-01
- Shared scene layout, output options, semantic load helpers, themes, label placement, and semantic SVG grouping.

## [0.1.0] - 2026-09-01
- Initial public library release.
