"""Backend-neutral scene layout for statics diagrams.

The renderers consume these resolved commands rather than each reimplementing
symbol geometry, label placement, and framing rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, pi, sin
from typing import TypeAlias

from .geometry import arrow_head, interpolate, rotate, spring_points, support_axes
from .model import Diagram, LabelPosition, Point, SupportKind, Vector, add, mul, normal, unit
from .options import RenderOptions
from .style import Style


@dataclass(frozen=True)
class Bounds:
    """An axis-aligned world-coordinate bounding box."""

    x0: float
    x1: float
    y0: float
    y1: float

    @classmethod
    def from_points(cls, points: list[Point], padding: float = 0.0) -> Bounds:
        xs, ys = zip(*points)
        return cls(min(xs) - padding, max(xs) + padding, min(ys) - padding, max(ys) + padding)

    def union(self, other: Bounds) -> Bounds:
        return Bounds(min(self.x0, other.x0), max(self.x1, other.x1), min(self.y0, other.y0), max(self.y1, other.y1))

    def padded(self, amount: float, vertical_ratio: float = 1.0) -> Bounds:
        return Bounds(self.x0 - amount, self.x1 + amount, self.y0 - amount * vertical_ratio, self.y1 + amount * vertical_ratio)

    @property
    def width(self) -> float:
        return max(self.x1 - self.x0, 1e-6)

    @property
    def height(self) -> float:
        return max(self.y1 - self.y0, 1e-6)

    def intersects(self, other: Bounds, padding: float = 0.0) -> bool:
        return not (
            self.x1 + padding <= other.x0
            or other.x1 + padding <= self.x0
            or self.y1 + padding <= other.y0
            or other.y1 + padding <= self.y0
        )


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point
    color: str
    width: float
    element_kind: str
    element_id: int
    dash: tuple[float, ...] | None = None

    def bounds(self) -> Bounds:
        return Bounds.from_points([self.start, self.end])


@dataclass(frozen=True)
class Polyline:
    points: tuple[Point, ...]
    color: str
    width: float
    element_kind: str
    element_id: int

    def bounds(self) -> Bounds:
        return Bounds.from_points(list(self.points))


@dataclass(frozen=True)
class Polygon:
    points: tuple[Point, ...]
    color: str
    width: float
    fill: str | None
    element_kind: str
    element_id: int

    def bounds(self) -> Bounds:
        return Bounds.from_points(list(self.points))


@dataclass(frozen=True)
class Circle:
    center: Point
    radius: float
    color: str
    width: float
    fill: str | None
    element_kind: str
    element_id: int

    def bounds(self) -> Bounds:
        return Bounds(self.center[0] - self.radius, self.center[0] + self.radius, self.center[1] - self.radius, self.center[1] + self.radius)


@dataclass(frozen=True)
class Text:
    point: Point
    value: str
    color: str
    size: float
    font_family: str
    align: str
    valign: str
    element_kind: str
    element_id: int
    bounds_box: Bounds

    def bounds(self) -> Bounds:
        return self.bounds_box


Command: TypeAlias = Line | Polyline | Polygon | Circle | Text


@dataclass
class Scene:
    commands: list[Command] = field(default_factory=list)
    bounds: Bounds | None = None

    def add(self, command: Command) -> None:
        self.commands.append(command)
        command_bounds = command.bounds()
        self.bounds = command_bounds if self.bounds is None else self.bounds.union(command_bounds)

    def occupied(self) -> list[Bounds]:
        return [command.bounds() for command in self.commands]


def _text_bounds(point: Point, value: str, scale: float, align: str, valign: str, multiplier: float = 1.0) -> Bounds:
    height = scale * 0.68 * multiplier
    width = max(len(value), 1) * scale * 0.36 * multiplier
    x0 = point[0] - {"left": 0.0, "center": width / 2, "right": width}[align]
    y0 = point[1] - {"top": height, "center": height / 2, "bottom": 0.0}[valign]
    return Bounds(x0, x0 + width, y0, y0 + height)


def _text_command(
    point: Point,
    value: str,
    *,
    color: str,
    style: Style,
    scale: float,
    element_kind: str,
    element_id: int,
    align: str = "center",
    valign: str = "bottom",
    multiplier: float = 1.0,
) -> Text:
    return Text(
        point,
        value,
        color,
        style.text_size * multiplier,
        style.font_family,
        align,
        valign,
        element_kind,
        element_id,
        _text_bounds(point, value, scale, align, valign, multiplier),
    )


def _add_arrow(
    scene: Scene,
    start: Point,
    vector: Vector,
    *,
    color: str,
    width: float,
    head_size: float,
    element_kind: str,
    element_id: int,
) -> None:
    end = add(start, vector)
    scene.add(Line(start, end, color, width, element_kind, element_id))
    left, right = arrow_head(end, vector, head_size)
    scene.add(Polygon((end, left, right), color, width * 0.7, color, element_kind, element_id))


def _add_ground(
    scene: Scene,
    center: Point,
    tangent: Vector,
    down: Vector,
    width: float,
    *,
    style: Style,
    element_kind: str,
    element_id: int,
) -> None:
    scene.add(Line(add(center, mul(tangent, -width / 2)), add(center, mul(tangent, width / 2)), style.ground, 1.2, element_kind, element_id))
    for ratio in (-0.38, -0.13, 0.13, 0.38):
        base = add(center, mul(tangent, width * ratio))
        scene.add(
            Line(
                base,
                add(add(base, mul(tangent, -width * 0.10)), mul(down, width * 0.14)),
                style.ground,
                0.9,
                element_kind,
                element_id,
            )
        )


def _anchor_offset(position: LabelPosition, scale: float) -> Vector:
    distance = scale * 0.8
    return {
        "above": (0.0, distance),
        "below": (0.0, -distance),
        "left": (-distance, 0.0),
        "right": (distance, 0.0),
        "center": (0.0, 0.0),
    }[position]


def _add_label(
    scene: Scene,
    value: str | None,
    *,
    base: Point,
    default_offset: Vector,
    position: LabelPosition,
    explicit_offset: Vector | None,
    color: str,
    style: Style,
    scale: float,
    element_kind: str,
    element_id: int,
    options: RenderOptions,
) -> None:
    if not value:
        return
    if explicit_offset is not None:
        candidates = [(add(base, explicit_offset), "bottom")]
    elif position != "auto":
        valign = "center" if position in {"left", "right", "center"} else ("bottom" if position == "above" else "top")
        candidates = [(add(base, _anchor_offset(position, scale)), valign)]
    else:
        candidates = [
            (add(base, default_offset), "bottom"),
            (add(base, _anchor_offset("above", scale)), "bottom"),
            (add(base, _anchor_offset("right", scale)), "center"),
            (add(base, _anchor_offset("left", scale)), "center"),
            (add(base, _anchor_offset("below", scale)), "top"),
            (add(base, (scale * 0.95, scale * 0.95)), "center"),
            (add(base, (-scale * 0.95, scale * 0.95)), "center"),
            (add(base, (scale * 0.95, -scale * 0.95)), "center"),
            (add(base, (-scale * 0.95, -scale * 0.95)), "center"),
        ]
    location, valign = candidates[0]
    if options.avoid_label_collisions:
        occupied = scene.occupied()
        for candidate, candidate_valign in candidates:
            candidate_bounds = _text_bounds(candidate, value, scale, "center", candidate_valign)
            if not any(candidate_bounds.intersects(box, scale * 0.08) for box in occupied):
                location, valign = candidate, candidate_valign
                break
    scene.add(
        _text_command(
            location,
            value,
            color=color,
            style=style,
            scale=scale,
            element_kind=element_kind,
            element_id=element_id,
            valign=valign,
        )
    )


def _add_support(scene: Scene, support, scale: float, *, style: Style, element_id: int) -> tuple[Point, Vector]:
    point = support.point
    tangent, down = support_axes(support.angle)
    height, width = scale * 1.55, scale * 1.75
    kind = "support"
    if support.kind is SupportKind.FIXED:
        base_direction = {
            "left": (-1.0, 0.0),
            "right": (1.0, 0.0),
            "top": (0.0, 1.0),
            "bottom": (0.0, -1.0),
        }[support.fixed_side]
        direction = rotate(base_direction, support.angle)
        cross = normal(direction)
        end = add(point, mul(direction, scale * 0.2))
        scene.add(Line(end, add(end, mul(cross, scale * 2)), style.ink, style.beam_width + 0.9, kind, element_id))
        for marker in (-0.85, -0.45, -0.05, 0.35, 0.75):
            root = add(end, mul(cross, scale * marker))
            scene.add(Line(root, add(add(root, mul(cross, scale * 0.22)), mul(direction, scale * 0.30)), style.ground, 1.0, kind, element_id))
        return point, direction
    if support.kind is SupportKind.SPRING:
        end = add(point, mul(down, height * 1.35))
        scene.add(Polyline(tuple(spring_points(point, down, height * 1.35, width * 0.22)), style.ink, 1.3, kind, element_id))
        _add_ground(scene, end, tangent, down, width * 1.25, style=style, element_kind=kind, element_id=element_id)
        return point, down
    left = add(add(point, mul(down, height)), mul(tangent, -width / 2))
    right = add(add(point, mul(down, height)), mul(tangent, width / 2))
    scene.add(Polygon((point, right, left), style.ink, 1.5, None, kind, element_id))
    ground = add(point, mul(down, height))
    if support.kind is SupportKind.ROLLER:
        radius = scale * 0.28
        for sign in (-0.28, 0.28):
            center = add(add(ground, mul(tangent, width * sign)), mul(down, radius))
            scene.add(Circle(center, radius, style.ink, 1.25, style.background, kind, element_id))
        _add_ground(scene, add(ground, mul(down, radius * 2)), tangent, down, width * 1.35, style=style, element_kind=kind, element_id=element_id)
    else:
        _add_ground(scene, ground, tangent, down, width * 1.25, style=style, element_kind=kind, element_id=element_id)
    return point, down


def layout_scene(diagram: Diagram, *, style: Style, options: RenderOptions) -> Scene:
    """Resolve a semantic :class:`Diagram` into common render commands."""
    scene = Scene()
    scale = diagram.scale()
    labels: list[tuple[str, int, str | None, Point, Vector, LabelPosition, Vector | None, str]] = []

    for index, beam in enumerate(diagram.beams):
        scene.add(
            Line(
                beam.start,
                beam.end,
                style.ink,
                style.beam_width if beam.kind == "beam" else style.bar_width,
                "beam",
                index,
                style.beam_dash,
            )
        )
        midpoint = interpolate(beam.start, beam.end, 0.5)
        labels.append(("beam", index, beam.label, midpoint, mul(normal((beam.end[0] - beam.start[0], beam.end[1] - beam.start[1])), scale * style.label_scale), beam.label_position, beam.label_offset, style.ink))
    for index, support in enumerate(diagram.supports):
        base, direction = _add_support(scene, support, scale, style=style, element_id=index)
        labels.append(("support", index, support.label, base, mul(direction, scale * 3.2), support.label_position, support.label_offset, style.ink))
    for index, hinge in enumerate(diagram.hinges):
        radius = hinge.radius or scale * 0.32
        scene.add(Circle(hinge.point, radius, style.ink, 1.35, style.background, "hinge", index))
        labels.append(("hinge", index, hinge.label, hinge.point, (0, scale * 0.55), hinge.label_position, hinge.label_offset, style.ink))
    for index, load in enumerate(diagram.distributed_loads):
        direction = unit(load.direction)
        length = load.offset or scale * 3.0
        color = load.color or style.load
        top_a, top_b = add(load.start, mul(direction, -length)), add(load.end, mul(direction, -length))
        scene.add(Line(top_a, top_b, color, 1.0, "distributed-load", index, style.load_dash))
        for arrow_index in range(load.count):
            _add_arrow(scene, interpolate(top_a, top_b, arrow_index / (load.count - 1)), mul(direction, length), color=color, width=style.force_width, head_size=scale * style.arrow_head_scale * 0.92, element_kind="distributed-load", element_id=index)
        labels.append(("distributed-load", index, load.label, interpolate(top_a, top_b, 0.5), mul(normal(direction), scale * 0.45), load.label_position, load.label_offset, color))
    for index, load in enumerate(diagram.point_loads):
        color = load.color or style.load
        _add_arrow(scene, load.point, load.vector, color=color, width=style.force_width, head_size=scale * style.arrow_head_scale, element_kind="point-load", element_id=index)
        labels.append(("point-load", index, load.label, interpolate(load.point, add(load.point, load.vector), 0.53), mul(normal(load.vector), scale * 0.48), load.label_position, load.label_offset, color))
    for index, reaction in enumerate(diagram.reactions):
        color = reaction.color or style.reaction
        _add_arrow(scene, reaction.point, reaction.vector, color=color, width=style.force_width, head_size=scale * style.arrow_head_scale, element_kind="reaction", element_id=index)
        labels.append(("reaction", index, reaction.label, interpolate(reaction.point, add(reaction.point, reaction.vector), 0.53), mul(normal(reaction.vector), scale * 0.48), reaction.label_position, reaction.label_offset, color))
    for index, moment in enumerate(diagram.moments):
        radius, color = moment.radius or scale * 1.05, moment.color or style.load
        start_angle, end_angle = (315, 35) if moment.clockwise else (35, 315)
        angles = [start_angle + (end_angle - start_angle) * step / 24 for step in range(25)]
        points = tuple((moment.point[0] + radius * cos(angle * pi / 180), moment.point[1] + radius * sin(angle * pi / 180)) for angle in angles)
        scene.add(Polyline(points, color, style.force_width, "moment", index))
        theta = end_angle * pi / 180
        direction = (sin(theta), -cos(theta)) if moment.clockwise else (-sin(theta), cos(theta))
        _add_arrow(scene, add(points[-1], mul(direction, -scale * 0.55)), mul(direction, scale * 0.55), color=color, width=style.force_width, head_size=scale * style.arrow_head_scale * 0.92, element_kind="moment", element_id=index)
        labels.append(("moment", index, moment.label, moment.point, (radius + scale * 0.45, radius * 0.35), moment.label_position, moment.label_offset, color))
    for index, dimension in enumerate(diagram.dimensions):
        normal_vector = normal((dimension.end[0] - dimension.start[0], dimension.end[1] - dimension.start[1]))
        start, end = add(dimension.start, mul(normal_vector, dimension.offset)), add(dimension.end, mul(normal_vector, dimension.offset))
        scene.add(Line(start, end, style.dimension, 1.0, "dimension", index, style.dimension_dash))
        tick = scale * 0.22
        for point in (start, end):
            scene.add(Line(add(point, mul(normal_vector, -tick)), add(point, mul(normal_vector, tick)), style.dimension, 1.0, "dimension", index))
        labels.append(("dimension", index, dimension.label, interpolate(start, end, 0.5), mul(normal_vector, scale * 0.38), dimension.label_position, dimension.label_offset, style.dimension))
    for index, text in enumerate(diagram.texts):
        scene.add(_text_command(text.point, text.value, color=style.ink, style=style, scale=scale, element_kind="text", element_id=index, align=text.align, valign=text.valign))

    for kind, index, value, base, default_offset, position, explicit_offset, color in labels:
        _add_label(scene, value, base=base, default_offset=default_offset, position=position, explicit_offset=explicit_offset, color=color, style=style, scale=scale, element_kind=kind, element_id=index, options=options)

    content_bounds = scene.bounds or Bounds(-1, 1, -1, 1)
    if diagram.title:
        title_point = ((content_bounds.x0 + content_bounds.x1) / 2, content_bounds.y1 + scale * 1.05)
        scene.add(_text_command(title_point, diagram.title, color=style.ink, style=style, scale=scale, element_kind="title", element_id=0, multiplier=1.25))
        content_bounds = scene.bounds or content_bounds
    margin = max(scale * options.padding, 0.4)
    scene.bounds = content_bounds.padded(margin, vertical_ratio=1.15)
    return scene


def figure_size(bounds: Bounds, options: RenderOptions) -> tuple[float, float]:
    """Return a non-letterboxed physical size for the common scene bounds."""
    aspect = bounds.width / bounds.height
    if options.width is not None and options.height is not None:
        return options.width, options.height
    if options.width is not None:
        return options.width, options.width / aspect
    assert options.height is not None
    return options.height * aspect, options.height
