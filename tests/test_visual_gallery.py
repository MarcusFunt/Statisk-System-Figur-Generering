"""End-to-end visual smoke test covering five representative diagram families."""

from __future__ import annotations

from collections.abc import Callable

from statics_diagrams import (
    COLORBLIND_STYLE,
    PRINT_STYLE,
    Diagram,
    RenderOptions,
    SupportKind,
    render_matplotlib,
    render_svg,
)


def _beam_with_mixed_loads() -> Diagram:
    return (
        Diagram(title="Simply supported beam")
        .beam((0, 0), (8, 0), label="AB", label_position="above")
        .support((0, 0), SupportKind.PIN, label="A")
        .support((8, 0), SupportKind.ROLLER, label="B")
        .force(at=(2.8, 0), direction=(0, -1), length=1.6, label="P")
        .udl((4.6, 0), (7.2, 0), direction=(0, -1), height=1.2, label="q")
        .reaction((0, 0), (0, 1.1), label="Aᵧ")
        .reaction((8, 0), (0, 1.1), label="Bᵧ")
        .dimension((0, -1.5), (8, -1.5), "L = 8 m")
    )


def _rotated_fixed_frame() -> Diagram:
    return (
        Diagram(title="Inclined fixed support")
        .beam((0, 0), (5, 2.2), label="Member", label_position="below")
        .support((0, 0), SupportKind.FIXED, fixed_side="left", angle=30, label="A")
        .support((5, 2.2), SupportKind.ROLLER, angle=30, label="B")
        .force(at=(2.5, 1.1), direction=(-0.3, -1), length=1.4, label="F")
    )


def _moment_only() -> Diagram:
    return Diagram(title="Applied moment").moment((10, 10), radius=2.0, clockwise=True, label="M")


def _dense_annotation_case() -> Diagram:
    return (
        Diagram(title="Annotated truss")
        .beam((0, 0), (3, 2.3), kind="bar")
        .beam((3, 2.3), (6, 0), kind="bar")
        .beam((0, 0), (6, 0), kind="bar")
        .hinge((0, 0), label="A")
        .hinge((3, 2.3), label="C")
        .hinge((6, 0), label="B")
        .support((0, 0), SupportKind.PIN)
        .support((6, 0), SupportKind.ROLLER)
        .force(at=(3, 2.3), direction=(0, -1), length=1.6, label="P", label_position="right")
        .dimension((0, -0.9), (6, -0.9), "6 m")
    )


def _print_theme_portal() -> Diagram:
    return (
        Diagram(title="Portal-frame load case")
        .beam((0, 0), (0, 4))
        .beam((0, 4), (6, 4))
        .beam((6, 4), (6, 0))
        .support((0, 0), SupportKind.FIXED, fixed_side="bottom", label="A")
        .support((6, 0), SupportKind.PIN, label="B")
        .udl((0.6, 4), (5.4, 4), direction=(0, -1), height=0.9, label="q")
        .moment((5.0, 5.7), clockwise=False, label="M")
    )


CASES: dict[str, Callable[[], Diagram]] = {
    "beam_with_mixed_loads": _beam_with_mixed_loads,
    "rotated_fixed_frame": _rotated_fixed_frame,
    "moment_only": _moment_only,
    "dense_annotation_case": _dense_annotation_case,
    "print_theme_portal": _print_theme_portal,
}


def test_visual_gallery_generates_five_figures(tmp_path):
    """Generate PNG and editable SVG output for five distinct visual scenarios."""
    options = RenderOptions(width=7, dpi=180, background="white")
    for name, make_diagram in CASES.items():
        diagram = make_diagram()
        style = PRINT_STYLE if name == "print_theme_portal" else COLORBLIND_STYLE
        figure = render_matplotlib(diagram, style=style, options=options)
        png_path = tmp_path / f"{name}.png"
        svg_path = tmp_path / f"{name}.svg"
        figure.savefig(png_path, dpi=options.dpi, transparent=False)
        render_svg(diagram, style=style, options=options).save(svg_path)

        assert png_path.stat().st_size > 1_000
        assert svg_path.read_text(encoding="utf-8").count("data-kind") >= 1
