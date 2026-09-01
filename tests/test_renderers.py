from xml.etree import ElementTree

from statics_diagrams import Diagram, SupportKind, render_matplotlib, render_svg


def test_render_svg_has_real_vector_primitives():
    diagram = (
        Diagram()
        .beam((0, 0), (4, 0))
        .support((0, 0), SupportKind.PIN)
        .support((4, 0), SupportKind.ROLLER)
        .point_load((2, 1), (0, -1), label="P")
    )
    svg = render_svg(diagram).content
    assert svg.startswith("<svg")
    assert "<polygon" in svg  # Support / arrowhead.
    assert "<path" in svg
    assert "P</text>" in svg
    ElementTree.fromstring(svg)


def test_matplotlib_figure_renders():
    diagram = Diagram().beam((0, 0), (4, 0)).support((0, 0), "pin").support((4, 0), "roller")
    figure = render_matplotlib(diagram)
    figure.canvas.draw()
    assert figure.axes[0].axison is False


def test_spring_and_fixed_symbols_render():
    diagram = Diagram().beam((0, 0), (4, 0)).support((0, 0), "fixed", fixed_side="left").support((4, 0), "spring")
    svg = render_svg(diagram).content
    assert "<polyline" in svg
