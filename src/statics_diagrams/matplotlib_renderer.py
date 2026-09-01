"""Matplotlib output for :mod:`statics_diagrams`."""

from __future__ import annotations

from math import cos, pi, sin

from matplotlib import pyplot as plt
from matplotlib.patches import Arc, Circle, FancyArrowPatch, Polygon

from .geometry import interpolate, spring_points, support_axes
from .model import Diagram, SupportKind, add, mul, normal, unit
from .style import DEFAULT_STYLE, Style


def _line(ax, points, *, color, width, **kwargs):
    xs, ys = zip(*points)
    return ax.plot(
        xs,
        ys,
        color=color,
        linewidth=width,
        solid_capstyle="round",
        solid_joinstyle="round",
        **kwargs,
    )


def _text(ax, point, value, *, style: Style, color=None, ha="center", va="bottom"):
    ax.text(*point, value, color=color or style.ink, fontsize=style.text_size, ha=ha, va=va, family="DejaVu Sans")


def _arrow(ax, start, vector, *, color, style: Style, label=None):
    end = add(start, vector)
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=style.force_width,
        color=color,
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(arrow)
    if label:
        midpoint = interpolate(start, end, 0.53)
        offset = mul(normal(vector), max(0.09, max(abs(vector[0]), abs(vector[1])) * 0.11))
        _text(ax, add(midpoint, offset), label, style=style, color=color)


def _draw_ground(ax, center, tangent, down, width, *, style: Style):
    a, b = add(center, mul(tangent, -width / 2)), add(center, mul(tangent, width / 2))
    _line(ax, [a, b], color=style.ground, width=1.2)
    for ratio in (-0.38, -0.13, 0.13, 0.38):
        base = add(center, mul(tangent, width * ratio))
        _line(
            ax,
            [base, add(add(base, mul(tangent, -width * 0.10)), mul(down, width * 0.14))],
            color=style.ground,
            width=0.9,
        )


def _draw_support(ax, support, scale, *, style: Style):
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
        _line(ax, [end, add(end, mul(cross, scale * 2.0))], color=style.ink, width=style.beam_width + 0.9)
        for marker in (-0.85, -0.45, -0.05, 0.35, 0.75):
            root = add(end, mul(cross, scale * marker))
            _line(
                ax,
                [root, add(add(root, mul(cross, scale * 0.22)), mul(direction, scale * 0.30))],
                color=style.ground,
                width=1.0,
            )
    else:
        left = add(add(point, mul(down, height)), mul(tangent, -width / 2))
        right = add(add(point, mul(down, height)), mul(tangent, width / 2))
        ground = add(point, mul(down, height))
        if support.kind is SupportKind.SPRING:
            points = spring_points(point, down, height * 1.35, width * 0.22)
            _line(ax, points, color=style.ink, width=1.3)
            _draw_ground(ax, points[-1], tangent, down, width * 1.25, style=style)
        else:
            ax.add_patch(Polygon([point, right, left], closed=True, fill=False, linewidth=1.5, edgecolor=style.ink, joinstyle="round"))
        if support.kind is SupportKind.ROLLER:
            radius = scale * 0.28
            for sign in (-0.28, 0.28):
                center = add(add(ground, mul(tangent, width * sign)), mul(down, radius))
                ax.add_patch(Circle(center, radius, fill=False, linewidth=1.25, edgecolor=style.ink))
            _draw_ground(ax, add(ground, mul(down, radius * 2)), tangent, down, width * 1.35, style=style)
        elif support.kind is SupportKind.PIN:
            _draw_ground(ax, ground, tangent, down, width * 1.25, style=style)
    if support.label:
        _text(ax, add(point, mul(down, height + scale * 0.8)), support.label, style=style, va="top")


def _draw_dimension(ax, dimension, scale, *, style: Style):
    a, b = dimension.start, dimension.end
    vector = (b[0] - a[0], b[1] - a[1])
    normal_vector = normal(vector)
    offset = mul(normal_vector, dimension.offset)
    a, b = add(a, offset), add(b, offset)
    _line(ax, [a, b], color=style.dimension, width=1.0)
    tick = scale * 0.22
    for point in (a, b):
        _line(ax, [add(point, mul(normal_vector, -tick)), add(point, mul(normal_vector, tick))], color=style.dimension, width=1.0)
    midpoint = interpolate(a, b, 0.5)
    _text(ax, add(midpoint, mul(normal_vector, scale * 0.38)), dimension.label, style=style, color=style.dimension)


def render_matplotlib(diagram: Diagram, *, ax=None, style: Style = DEFAULT_STYLE, padding: float = 3.0):
    """Render ``diagram`` and return its Matplotlib figure.

    Pass an existing ``ax`` to place the diagram into a report layout. Otherwise
    the function creates a transparent, axis-free figure suited to export.
    """
    own_figure = ax is None
    if own_figure:
        figure, ax = plt.subplots(figsize=(10, 4.5))
    else:
        figure = ax.figure
    scale = diagram.scale()

    for beam in diagram.beams:
        width = style.beam_width if beam.kind == "beam" else style.bar_width
        _line(ax, [beam.start, beam.end], color=style.ink, width=width)
        if beam.label:
            midpoint = interpolate(beam.start, beam.end, 0.5)
            _text(
                ax,
                add(midpoint, mul(normal((beam.end[0] - beam.start[0], beam.end[1] - beam.start[1])), scale * 0.62)),
                beam.label,
                style=style,
            )
    for support in diagram.supports:
        _draw_support(ax, support, scale, style=style)
    for hinge in diagram.hinges:
        radius = hinge.radius or scale * 0.32
        ax.add_patch(Circle(hinge.point, radius, facecolor="white", edgecolor=style.ink, linewidth=1.35, zorder=5))
        if hinge.label:
            _text(ax, add(hinge.point, (0, scale * 0.55)), hinge.label, style=style)
    for load in diagram.distributed_loads:
        direction = unit(load.direction)
        length = load.offset or scale * 3.0
        color = load.color or style.load
        top_a, top_b = add(load.start, mul(direction, -length)), add(load.end, mul(direction, -length))
        _line(ax, [top_a, top_b], color=color, width=1.0)
        for index in range(load.count):
            start = interpolate(top_a, top_b, index / (load.count - 1))
            _arrow(ax, start, mul(direction, length), color=color, style=style)
        if load.label:
            _text(ax, add(interpolate(top_a, top_b, 0.5), mul(normal(direction), scale * 0.45)), load.label, style=style, color=color)
    for load in diagram.point_loads:
        _arrow(ax, load.point, load.vector, color=load.color or style.load, style=style, label=load.label)
    for reaction in diagram.reactions:
        _arrow(ax, reaction.point, reaction.vector, color=reaction.color or style.reaction, style=style, label=reaction.label)
    for moment in diagram.moments:
        radius = moment.radius or scale * 1.05
        color = moment.color or style.load
        arc = Arc(moment.point, radius * 2, radius * 2, angle=0, theta1=35, theta2=315, linewidth=style.force_width, color=color)
        ax.add_patch(arc)
        angle = 315 if moment.clockwise else 35
        sign = -1 if moment.clockwise else 1
        theta = angle * pi / 180
        tip = (moment.point[0] + radius * cos(theta), moment.point[1] + radius * sin(theta))
        tangent = (-sin(theta) * sign, cos(theta) * sign)
        _arrow(ax, add(tip, mul(tangent, -scale * 0.55)), mul(tangent, scale * 0.55), color=color, style=style)
        if moment.label:
            _text(ax, add(moment.point, (radius + scale * 0.45, radius * 0.35)), moment.label, style=style, color=color)
    for dimension in diagram.dimensions:
        _draw_dimension(ax, dimension, scale, style=style)
    for text in diagram.texts:
        _text(ax, text.point, text.value, style=style, ha=text.align, va=text.valign)

    x0, x1, y0, y1 = diagram.extent()
    margin = max(scale * padding, 0.4)
    ax.set_xlim(x0 - margin, x1 + margin)
    ax.set_ylim(y0 - margin * 1.25, y1 + margin * 1.25)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    if diagram.title:
        ax.set_title(diagram.title, color=style.ink, fontsize=13, pad=14, weight="semibold")
    if own_figure:
        figure.tight_layout(pad=0.45)
    return figure
