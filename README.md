# statics-diagrams

`statics-diagrams` is a small, analysis-free Python library for producing
clear statics and strength-of-materials figures. It provides the familiar
symbol vocabulary—beams, supports, hinges, springs, loads, reactions,
dimensions, and labels—without needing LaTeX or a structural solver.

It can render to:

- Matplotlib figures for PNG, PDF, and SVG export.
- Standalone SVG documents that remain editable in vector-graphics tools.

## Installation

```bash
pip install statics-diagrams
```

For development, clone the repository and install the development extras:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
from statics_diagrams import Diagram, RenderOptions, SupportKind, render_matplotlib, render_svg

diagram = Diagram(title="Simply supported beam")
diagram.beam((0, 0), (8, 0), label="AB")
diagram.support((0, 0), SupportKind.PIN, label="A")
diagram.support((8, 0), SupportKind.ROLLER, label="B")
diagram.force(at=(3.5, 0), direction=(0, -1), length=1.4, label="F")
diagram.udl((4.5, 0), (7.2, 0), direction=(0, -1), height=1.0, label="q")
diagram.dimension((0, -1.45), (8, -1.45), "L")

options = RenderOptions(width=7, dpi=220, background="white")
render_matplotlib(diagram, options=options).savefig("beam.png", dpi=options.dpi)
render_svg(diagram, options=options).save("beam.svg")
```

Coordinates are drawing coordinates: no stiffness, material, units, or
calculation model is implied. Positive `x` is right and positive `y` is up.
For point loads and reactions, a vector points in the arrowhead direction.

## Layout, labels, and styling

Both renderers use the same resolved scene layout. It calculates the drawing
bounds from every symbol, marker, label, and title, so standalone moments and
labels at the edge of a diagram are framed correctly. SVG exports use semantic
`<g>` elements with stable `id` and `data-kind` attributes for easier editing.

Use `label_position` (`"above"`, `"below"`, `"left"`, `"right"`, or
`"center"`) or `label_offset=(dx, dy)` on labelled primitives when you want
direct placement. Automatic labels try clear alternatives by default; pass
`RenderOptions(avoid_label_collisions=False)` to retain deterministic default
placement.

`RenderOptions` gives both renderers the same physical width/height, DPI,
padding, and background behaviour. Omitting one dimension derives it from the
laid-out aspect ratio, avoiding a fixed, letterboxed canvas. `background=None`
creates a transparent canvas.

The public `Style` class controls colours, line widths and dash patterns,
marker size, fonts, and the hinge fill. Built-in themes are `DEFAULT_STYLE`,
`MONOCHROME_STYLE`, `PRINT_STYLE`, and `COLORBLIND_STYLE`.

Use `force(at=..., direction=..., length=...)` for a semantic point force: its
arrowhead is guaranteed to land at `at`. `udl(..., direction=..., height=...)`
does the same for uniformly distributed loads. The original `point_load` and
`distributed_load` methods remain available as low-level drawing primitives.

## Development

```bash
python -m pytest
python -m ruff check .
python examples/gallery.py
```

The gallery writes generated files to `examples/output/`, which is deliberately
not tracked. Continuous integration runs the test suite and lint checks on
supported Python versions.

## License

Released under the [MIT License](LICENSE).
