from __future__ import annotations

from statics_diagrams import COLORBLIND_STYLE, Diagram, RenderOptions, render_svg
from statics_diagrams.layout import Arc, Bounds, Circle, ElementGroup, Line, Paint, Polygon, Scene, Text, layout_scene


def _group(scene: Scene, kind: str) -> ElementGroup:
    return next(group for group in scene.groups if group.element_kind == kind)


def test_line_collision_bounds_include_the_visible_stroke_envelope() -> None:
    line = Line((0.0, 0.0), (2.0, 0.0), paint=Paint("black", 10.0))
    scene = Scene(groups=[ElementGroup("line", 0, 0, 0, commands=[line])], scale=1.0)
    assert scene.occupied()[0].intersects(Bounds(0.5, 0.6, -0.02, 0.02))


def test_curved_members_and_moments_use_native_arc_commands() -> None:
    scene = layout_scene(
        Diagram().curved_member((0, 0), 2, 20, 160).moment((5, 0), radius=1),
        style=COLORBLIND_STYLE,
        options=RenderOptions(width=6),
    )
    assert sum(isinstance(command, Arc) for command in scene.commands) == 2
    svg = render_svg(Diagram().curved_member((0, 0), 2, 20, 160).moment((5, 0), radius=1)).content
    assert svg.count(" A ") >= 2


def test_arc_bounds_include_exact_cardinal_extrema() -> None:
    arc = Arc((0, 0), 2, 20, 100, Paint("black", 1.0))
    bounds = arc.bounds()
    assert bounds.y1 == 2
    assert bounds.x0 < 0 < bounds.x1


def test_angle_dimensions_have_witness_lines_and_inward_arrowheads() -> None:
    scene = layout_scene(
        Diagram().angle_dimension((0, 0), 0, 90, 2, "θ"),
        style=COLORBLIND_STYLE,
        options=RenderOptions(width=6),
    )
    group = _group(scene, "angle-dimension")
    assert sum(isinstance(command, Arc) for command in group.commands) == 1
    assert sum(isinstance(command, Line) for command in group.commands) == 2
    assert sum(isinstance(command, Polygon) for command in group.commands) == 2


def test_leaders_start_at_the_measured_text_box_edge() -> None:
    scene = layout_scene(
        Diagram().leader((0, 0), (3, 1), "long annotation"),
        style=COLORBLIND_STYLE,
        options=RenderOptions(width=6),
    )
    group = _group(scene, "leader")
    text = next(command for command in group.commands if isinstance(command, Text))
    shaft = next(command for command in group.commands if isinstance(command, Line))
    assert not text.bounds_box.intersects(Bounds(shaft.start[0], shaft.start[0], shaft.start[1], shaft.start[1]))


def test_default_downward_udl_label_is_outside_the_load_envelope() -> None:
    scene = layout_scene(
        Diagram().udl((0, 0), (4, 0), direction=(0, -1), height=1, label="q"),
        style=COLORBLIND_STYLE,
        options=RenderOptions(width=6, avoid_label_collisions=False),
    )
    text = next(command for command in scene.commands if isinstance(command, Text) and command.value == "q")
    assert text.point[1] > 1


def test_dimension_defaults_are_scale_relative_and_explicit_values_survive_transforms() -> None:
    diagram = Diagram().dimension((0, 0), (4, 0), "L", offset=1)
    assert diagram.elements[0].extension_gap is None
    scene = layout_scene(diagram, style=COLORBLIND_STYLE, options=RenderOptions(width=6))
    group = _group(scene, "dimension")
    extension = [command for command in group.commands if isinstance(command, Line)][1]
    assert extension.start[1] > 0
    explicit = Diagram().dimension((0, 0), (4, 0), "L", offset=1, extension_gap=0.2)
    transformed = Diagram().add_group(explicit, scale=2)
    assert transformed.elements[0].extension_gap == 0.4


def test_annotation_extents_include_axis_and_displacement_endpoints() -> None:
    diagram = Diagram().axes((0, 0), x_length=4, y_length=3).displacement((1, 1), (5, -4))
    x0, x1, y0, y1 = diagram.extent()
    assert (x0, x1, y0, y1) == (0, 6, -3, 3)


def test_link_joints_are_larger_than_the_previous_minimal_marker() -> None:
    scene = layout_scene(Diagram().link((0, 0), (4, 0)), style=COLORBLIND_STYLE, options=RenderOptions(width=6))
    circles = [command for command in _group(scene, "link").commands if isinstance(command, Circle)]
    assert len(circles) == 2
    assert circles[0].radius == scene.scale * 0.26


def test_svg_emits_font_fallbacks_for_editable_text() -> None:
    svg = render_svg(Diagram().text((0, 0), "label")).content
    assert 'font-family="DejaVu Sans, Arial, sans-serif"' in svg


def test_leaders_reject_zero_length_geometry() -> None:
    try:
        Diagram().leader((0, 0), (0, 0), "invalid")
    except ValueError as error:
        assert "distinct" in str(error)
    else:
        raise AssertionError("zero-length leader was accepted")
