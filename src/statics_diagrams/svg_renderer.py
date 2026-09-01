"""Dependency-free standalone SVG output for :mod:`statics_diagrams`."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import cos, pi, sin
from pathlib import Path

from .geometry import arrow_head, interpolate, spring_points, support_axes
from .model import Diagram, SupportKind, add, mul, normal, unit
from .style import DEFAULT_STYLE, Style


def _f(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


@dataclass
class SVGDocument:
    """A complete SVG document returned by :func:`render_svg`."""

    content: str

    def save(self, path: str | Path) -> Path:
        """Write the document to ``path`` and return the resolved path object."""
        output = Path(path)
        output.write_text(self.content, encoding="utf-8")
        return output


class _Canvas:
    def __init__(
        self,
        x0: float,
        y0: float,
        width: float,
        height: float,
        pixels_per_unit: float,
        style: Style,
    ) -> None:
        self.x0, self.y0, self.ppu = x0, y0, pixels_per_unit
        self.width, self.height = width * pixels_per_unit, height * pixels_per_unit
        self.style = style
        self.parts: list[str] = []

    def point(self, point: tuple[float, float]) -> tuple[float, float]:
        return ((point[0] - self.x0) * self.ppu, (self.y0 - point[1]) * self.ppu)

    def line(
        self,
        a: tuple[float, float],
        b: tuple[float, float],
        *,
        color: str,
        width: float,
        dash: str | None = None,
    ) -> None:
        ax, ay = self.point(a)
        bx, by = self.point(b)
        dashed = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<path d="M {_f(ax)} {_f(ay)} L {_f(bx)} {_f(by)}" fill="none" '
            f'stroke="{color}" stroke-width="{_f(width)}" stroke-linecap="round" '
            f'stroke-linejoin="round"{dashed}/>'
        )

    def polyline(
        self,
        points: list[tuple[float, float]],
        *,
        color: str,
        width: float,
        fill: str = "none",
    ) -> None:
        encoded = " ".join(f"{_f(x)} {_f(y)}" for x, y in map(self.point, points))
        self.parts.append(
            f'<polyline points="{encoded}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{_f(width)}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def polygon(
        self,
        points: list[tuple[float, float]],
        *,
        color: str,
        width: float,
        fill: str = "none",
    ) -> None:
        encoded = " ".join(f"{_f(x)} {_f(y)}" for x, y in map(self.point, points))
        self.parts.append(
            f'<polygon points="{encoded}" fill="{fill}" stroke="{color}" '
            f'stroke-width="{_f(width)}" stroke-linejoin="round"/>'
        )

    def circle(
        self,
        point: tuple[float, float],
        radius: float,
        *,
        color: str,
        width: float,
        fill: str = "white",
    ) -> None:
        x, y = self.point(point)
        self.parts.append(
            f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(radius * self.ppu)}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{_f(width)}"/>'
        )

    def text(
        self,
        point: tuple[float, float],
        value: str,
        *,
        color: str,
        size: float,
        anchor: str = "middle",
        baseline: str = "auto",
    ) -> None:
        x, y = self.point(point)
        attrs = f' text-anchor="{anchor}" dominant-baseline="{baseline}"'
        self.parts.append(
            f'<text x="{_f(x)}" y="{_f(y)}" fill="{color}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{_f(size)}"{attrs}>'
            f"{escape(value)}</text>"
        )

    def arrow(
        self,
        start: tuple[float, float],
        vector: tuple[float, float],
        *,
        color: str,
        width: float,
        head_size: float,
    ) -> None:
        end = add(start, vector)
        self.line(start, end, color=color, width=width)
        a, b = arrow_head(end, vector, head_size)
        self.polygon([end, a, b], color=color, width=width * 0.7, fill=color)


def _ground(
    canvas: _Canvas,
    center: tuple[float, float],
    tangent: tuple[float, float],
    down: tuple[float, float],
    width: float,
    *,
    style: Style,
) -> None:
    a, b = add(center, mul(tangent, -width / 2)), add(center, mul(tangent, width / 2))
    canvas.line(a, b, color=style.ground, width=1.2)
    for ratio in (-0.38, -0.13, 0.13, 0.38):
        base = add(center, mul(tangent, width * ratio))
        canvas.line(
            base,
            add(add(base, mul(tangent, -width * 0.10)), mul(down, width * 0.14)),
            color=style.ground,
            width=0.9,
        )


def _support(canvas: _Canvas, support, scale: float, *, style: Style) -> None:
    point = support.point
    tangent, down = support_axes(support.angle)
    height, width = scale * 1.55, scale * 1.75
    if support.kind is SupportKind.FIXED:
        direction = {
            "left": (-1, 0),
            "right": (1, 0),
            "top": (0, 1),
            "bottom": (0, -1),
        }[support.fixed_side]
        end = add(point, mul(direction, scale * 0.2))
        cross = normal(direction)
        canvas.line(end, add(end, mul(cross, scale * 2)), color=style.ink, width=style.beam_width + 0.9)
        for marker in (-0.85, -0.45, -0.05, 0.35, 0.75):
            root = add(end, mul(cross, scale * marker))
            canvas.line(
                root,
                add(add(root, mul(cross, scale * 0.22)), mul(direction, scale * 0.30)),
                color=style.ground,
                width=1.0,
            )
    elif support.kind is SupportKind.SPRING:
        end = add(point, mul(down, height * 1.35))
        canvas.polyline(
            spring_points(point, down, height * 1.35, width * 0.22), color=style.ink, width=1.3
        )
        _ground(canvas, end, tangent, down, width * 1.25, style=style)
    else:
        left = add(add(point, mul(down, height)), mul(tangent, -width / 2))
        right = add(add(point, mul(down, height)), mul(tangent, width / 2))
        canvas.polygon([point, right, left], color=style.ink, width=1.5)
        ground = add(point, mul(down, height))
        if support.kind is SupportKind.ROLLER:
            radius = scale * 0.28
            for sign in (-0.28, 0.28):
                canvas.circle(
                    add(add(ground, mul(tangent, width * sign)), mul(down, radius)),
                    radius,
                    color=style.ink,
                    width=1.25,
                    fill="white",
                )
            _ground(canvas, add(ground, mul(down, radius * 2)), tangent, down, width * 1.35, style=style)
        else:
            _ground(canvas, ground, tangent, down, width * 1.25, style=style)
    if support.label:
        canvas.text(
            add(point, mul(down, height + scale * 0.8)),
            support.label,
            color=style.ink,
            size=style.text_size,
            baseline="hanging",
        )


def render_svg(
    diagram: Diagram,
    *,
    style: Style = DEFAULT_STYLE,
    padding: float = 3.0,
    pixels_per_unit: float = 82.0,
) -> SVGDocument:
    """Return an editable standalone SVG document for ``diagram``."""
    scale = diagram.scale()
    x0, x1, y0, y1 = diagram.extent()
    margin = max(scale * padding, 0.4)
    x0, x1 = x0 - margin, x1 + margin
    y0, y1 = y0 - margin * 1.25, y1 + margin * 1.25
    canvas = _Canvas(x0, y1, x1 - x0, y1 - y0, pixels_per_unit, style)

    for beam in diagram.beams:
        width = style.beam_width if beam.kind == "beam" else style.bar_width
        canvas.line(beam.start, beam.end, color=style.ink, width=width)
        if beam.label:
            midpoint = interpolate(beam.start, beam.end, 0.5)
            canvas.text(
                add(midpoint, mul(normal((beam.end[0] - beam.start[0], beam.end[1] - beam.start[1])), scale * 0.62)),
                beam.label,
                color=style.ink,
                size=style.text_size,
            )
    for support in diagram.supports:
        _support(canvas, support, scale, style=style)
    for hinge in diagram.hinges:
        radius = hinge.radius or scale * 0.32
        canvas.circle(hinge.point, radius, color=style.ink, width=1.35)
        if hinge.label:
            canvas.text(add(hinge.point, (0, scale * 0.55)), hinge.label, color=style.ink, size=style.text_size)
    for load in diagram.distributed_loads:
        direction, length = unit(load.direction), load.offset or scale * 3.0
        color = load.color or style.load
        top_a, top_b = add(load.start, mul(direction, -length)), add(load.end, mul(direction, -length))
        canvas.line(top_a, top_b, color=color, width=1.0)
        for index in range(load.count):
            canvas.arrow(
                interpolate(top_a, top_b, index / (load.count - 1)),
                mul(direction, length),
                color=color,
                width=style.force_width,
                head_size=scale * 0.33,
            )
        if load.label:
            canvas.text(
                add(interpolate(top_a, top_b, 0.5), mul(normal(direction), scale * 0.45)),
                load.label,
                color=color,
                size=style.text_size,
            )
    for load in diagram.point_loads:
        color = load.color or style.load
        canvas.arrow(load.point, load.vector, color=color, width=style.force_width, head_size=scale * 0.36)
        if load.label:
            midpoint = interpolate(load.point, add(load.point, load.vector), 0.53)
            canvas.text(
                add(midpoint, mul(normal(load.vector), scale * 0.48)),
                load.label,
                color=color,
                size=style.text_size,
            )
    for reaction in diagram.reactions:
        color = reaction.color or style.reaction
        canvas.arrow(
            reaction.point,
            reaction.vector,
            color=color,
            width=style.force_width,
            head_size=scale * 0.36,
        )
        if reaction.label:
            midpoint = interpolate(reaction.point, add(reaction.point, reaction.vector), 0.53)
            canvas.text(
                add(midpoint, mul(normal(reaction.vector), scale * 0.48)),
                reaction.label,
                color=color,
                size=style.text_size,
            )
    for moment in diagram.moments:
        radius, color = moment.radius or scale * 1.05, moment.color or style.load
        start_angle, end_angle = (315, 35) if moment.clockwise else (35, 315)
        values = [start_angle + (end_angle - start_angle) * index / 18 for index in range(19)]
        points = [
            (moment.point[0] + radius * cos(angle * pi / 180), moment.point[1] + radius * sin(angle * pi / 180))
            for angle in values
        ]
        canvas.polyline(points, color=color, width=style.force_width)
        tip = points[-1]
        theta = end_angle * pi / 180
        direction = (sin(theta), -cos(theta)) if moment.clockwise else (-sin(theta), cos(theta))
        canvas.arrow(
            add(tip, mul(direction, -scale * 0.55)),
            mul(direction, scale * 0.55),
            color=color,
            width=style.force_width,
            head_size=scale * 0.33,
        )
        if moment.label:
            canvas.text(
                add(moment.point, (radius + scale * 0.45, radius * 0.35)),
                moment.label,
                color=color,
                size=style.text_size,
            )
    for dimension in diagram.dimensions:
        a, b = dimension.start, dimension.end
        normal_vector = normal((b[0] - a[0], b[1] - a[1]))
        a, b = add(a, mul(normal_vector, dimension.offset)), add(b, mul(normal_vector, dimension.offset))
        canvas.line(a, b, color=style.dimension, width=1.0)
        tick = scale * 0.22
        for point in (a, b):
            canvas.line(
                add(point, mul(normal_vector, -tick)),
                add(point, mul(normal_vector, tick)),
                color=style.dimension,
                width=1.0,
            )
        canvas.text(
            add(interpolate(a, b, 0.5), mul(normal_vector, scale * 0.38)),
            dimension.label,
            color=style.dimension,
            size=style.text_size,
        )
    for text in diagram.texts:
        canvas.text(
            text.point,
            text.value,
            color=style.ink,
            size=style.text_size,
            anchor={"left": "start", "center": "middle", "right": "end"}[text.align],
            baseline={"top": "hanging", "center": "middle", "bottom": "auto"}[text.valign],
        )

    title = f"<title>{escape(diagram.title)}</title>" if diagram.title else ""
    content = "\n".join(canvas.parts)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(canvas.width)}" '
        f'height="{_f(canvas.height)}" viewBox="0 0 {_f(canvas.width)} {_f(canvas.height)}" role="img">'
        f'{title}<rect width="100%" height="100%" fill="white"/>{content}</svg>\n'
    )
    return SVGDocument(svg)
