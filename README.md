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
from statics_diagrams import Diagram, SupportKind, render_matplotlib, render_svg

diagram = Diagram(title="Simply supported beam")
diagram.beam((0, 0), (8, 0), label="AB")
diagram.support((0, 0), SupportKind.PIN, label="A")
diagram.support((8, 0), SupportKind.ROLLER, label="B")
diagram.point_load((3.5, 1.4), (0, -1.4), label="F")
diagram.distributed_load((4.5, 0), (7.2, 0), direction=(0, -1), label="q")
diagram.dimension((0, -1.45), (8, -1.45), "L")

render_matplotlib(diagram).savefig("beam.png", dpi=220, bbox_inches="tight")
render_svg(diagram).save("beam.svg")
```

Coordinates are drawing coordinates: no stiffness, material, units, or
calculation model is implied. Positive `x` is right and positive `y` is up.
For point loads and reactions, a vector points in the arrowhead direction.

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
