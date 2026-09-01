# statics-diagrams

`statics-diagrams` is an **analysis-free** Python library for producing clean statics and strength-of-materials figures. It draws the system you describe; it does not calculate reactions, stiffness, or stresses.

The library has a dependency-free standalone SVG backend and an optional Matplotlib backend for PNG/PDF/SVG export.

## Installation

SVG only:

```bash
pip install statics-diagrams
```

With Matplotlib:

```bash
pip install "statics-diagrams[matplotlib]"
```

Development:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
from statics_diagrams import Diagram, RenderOptions, SupportKind, render_svg

beam = (
    Diagram(title="Simply supported beam")
    .beam((0, 0), (8, 0), label="AB")
    .support((0, 0), SupportKind.PIN, label="A")
    .support((8, 0), SupportKind.ROLLER, label="B")
    .force(at=(3.5, 0), direction=(0, -1), length=1.4, label="F")
    .udl((4.5, 0), (7.2, 0), direction=(0, -1), height=1.0, label="q")
    .dimension((0, -1.45), (8, -1.45), "L", offset=0.0)
)

render_svg(beam, options=RenderOptions(width=7, background=None)).save("beam.svg")
```

For Matplotlib:

```python
from statics_diagrams import render_matplotlib
fig = render_matplotlib(beam, options=RenderOptions(width=7, background="white"))
fig.savefig("beam.png", dpi=220)
```

## Drawing vocabulary

Core primitives include beams/bars, curved members, pin/roller/fixed/spring/guided/sliding supports, hinges, point loads, reactions, moments, uniform/triangular/trapezoidal distributed loads, dimensions, angle dimensions, standalone springs, links, coordinate axes, section markers, leader annotations, prescribed displacement arrows, and text.

Distributed-load arrow density is automatic by default and can be overridden with `count=N`.

## Ordered scene, layers, transforms, and styling

Calls are drawn in insertion order by default. Set `z_index=` only when you need an explicit layer override.

```python
diagram = Diagram()
with diagram.group(translate=(4, 2), rotate=30):
    diagram.beam((0, 0), (3, 0))
    diagram.support((0, 0), "pin")
```

Per-element styling uses `ElementStyle` and inherits all unspecified values from the global theme:

```python
from statics_diagrams import ElementStyle

diagram.beam((0, 0), (4, 0), style=ElementStyle(color="#0057b8", line_width=4), css_class="highlight")
```

Built-in themes are `DEFAULT_STYLE`, `MONOCHROME_STYLE`, `PRINT_STYLE`, and `COLORBLIND_STYLE`.

## Labels and text

Automatic labels use scored collision-aware candidate placement. Explicit `label_position=` or `label_offset=` remains authoritative. Multiline text using `\n` is supported by both backends.

Text is **literal by default**, including dollar signs. This avoids Matplotlib MathText producing output that standalone SVG cannot match. Prefer Unicode (`σ`, `Δ`, `Aᵧ`) for engineering notation until a shared explicit math-markup mode is added.

## SVG semantics

Each logical diagram element is emitted as one stable semantic `<g>` with `id` and `data-kind`. To inline multiple generated SVGs into the same HTML document, give each a namespace:

```python
RenderOptions(svg_id_prefix="beam-example-1")
```

All geometry uses a uniform world-to-output scale, even when both output width and height are specified.

The legacy `pixels_per_unit=` SVG argument retains its original meaning: the requested number of SVG viewBox units per drawing-space unit.

## Dimensions

Offset dimensions can draw witness/extension lines and choose endpoint styles:

```python
diagram.dimension(
    (0, 0), (8, 0), "8 m",
    offset=-1.2,
    extension_lines=True,
    endpoint_style="arrow",  # tick | arrow | slash | dot | none
)
```

## Development

```bash
python -m pytest
python -m ruff check .
python -m mypy src/statics_diagrams tests/typing_usage.py
python -m build
```

CI additionally tests the declared Matplotlib 3.7 dependency floor, a no-Matplotlib SVG-only install, built wheel/sdist artifacts, and deterministic scene-level visual regression snapshots.

## License

MIT.
