"""Generate a small gallery in ``examples/output``."""

from pathlib import Path

from statics_diagrams import Diagram, SupportKind, render_matplotlib, render_svg

OUTPUT = Path(__file__).parent / "output"


def save(name: str, diagram: Diagram) -> None:
    OUTPUT.mkdir(exist_ok=True)
    render_matplotlib(diagram).savefig(OUTPUT / f"{name}.png", dpi=220, bbox_inches="tight", transparent=True)
    render_svg(diagram).save(OUTPUT / f"{name}.svg")


def simple_beam() -> Diagram:
    diagram = Diagram(title="Simply supported beam")
    diagram.beam((0, 0), (8, 0), label="AB")
    diagram.support((0, 0), SupportKind.PIN, label="A")
    diagram.support((8, 0), SupportKind.ROLLER, label="B")
    diagram.point_load((3.1, 1.6), (0, -1.6), label="F")
    diagram.distributed_load((4.7, 0), (7.2, 0), direction=(0, -1), label="q")
    diagram.reaction((0, 0), (0, 1.1), label="Aᵧ")
    diagram.reaction((0, 0), (1.0, 0), label="Aₓ")
    diagram.reaction((8, 0), (0, 1.1), label="Bᵧ")
    diagram.dimension((0, -1.7), (8, -1.7), "L = 8 m")
    return diagram


def cantilever() -> Diagram:
    diagram = Diagram(title="Cantilever")
    diagram.beam((0, 0), (6, 0))
    diagram.support((0, 0), SupportKind.FIXED, fixed_side="left", label="A")
    diagram.distributed_load((1.0, 0), (5.4, 0), direction=(0, -1), label="q")
    diagram.moment((5.3, 0.75), clockwise=False, label="M")
    diagram.reaction((0, 0), (0, 1.15), label="Aᵧ")
    diagram.reaction((0, 0), (1.1, 0), label="Aₓ")
    return diagram


def portal_frame() -> Diagram:
    diagram = Diagram(title="Portal frame")
    diagram.beam((0, 0), (0, 4))
    diagram.beam((0, 4), (6, 4))
    diagram.beam((6, 4), (6, 0))
    diagram.support((0, 0), SupportKind.FIXED, fixed_side="bottom", label="A")
    diagram.support((6, 0), SupportKind.PIN, label="B")
    diagram.point_load((3.7, 5.4), (0, -1.4), label="P")
    diagram.distributed_load((0.5, 4), (5.5, 4), direction=(0, -1), label="q")
    return diagram


def truss() -> Diagram:
    diagram = Diagram(title="Simple truss")
    diagram.beam((0, 0), (3, 2.2), kind="bar")
    diagram.beam((3, 2.2), (6, 0), kind="bar")
    diagram.beam((0, 0), (6, 0), kind="bar")
    diagram.hinge((0, 0), label="A")
    diagram.hinge((3, 2.2), label="C")
    diagram.hinge((6, 0), label="B")
    diagram.support((0, 0), SupportKind.PIN)
    diagram.support((6, 0), SupportKind.ROLLER)
    diagram.point_load((3, 3.5), (0, -1.3), label="F")
    return diagram


if __name__ == "__main__":
    for name, maker in {
        "simple_beam": simple_beam,
        "cantilever": cantilever,
        "portal_frame": portal_frame,
        "truss": truss,
    }.items():
        save(name, maker())
    print(f"Wrote gallery to {OUTPUT}")
