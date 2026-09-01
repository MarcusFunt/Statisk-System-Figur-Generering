# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2026-09-01

### Added

- Shared scene layout used by both renderer backends, with complete primitive
  bounds, visible SVG titles, semantic SVG grouping, and collision-aware labels.
- `RenderOptions`, semantic `force` and `udl` helpers, named themes, label
  anchors/offsets, and rotated fixed supports.

### Changed

- Matplotlib and SVG now derive their default physical proportions from the
  same laid-out scene instead of using a fixed Matplotlib canvas.

## [0.1.0] - 2026-09-01

### Added

- Initial public library release with Matplotlib and standalone SVG renderers.
- Beam, support, hinge, spring, load, reaction, moment, dimension, and text primitives.
