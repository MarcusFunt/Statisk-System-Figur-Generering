"""Matplotlib output for the shared statics-diagrams scene."""

from __future__ import annotations

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle as MatplotlibCircle
from matplotlib.patches import Polygon as MatplotlibPolygon

from .layout import Circle, Line, Polygon, Polyline, Text, figure_size, layout_scene
from .model import Diagram
from .options import RenderOptions
from .style import DEFAULT_STYLE, Style


def _draw_command(ax, command) -> None:
    if isinstance(command, Line):
        xs, ys = zip(command.start, command.end)
        line, = ax.plot(
            xs,
            ys,
            color=command.color,
            linewidth=command.width,
            linestyle="solid",
            solid_capstyle="round",
            solid_joinstyle="round",
        )
        if command.dash:
            line.set_dashes(command.dash)
        return
    if isinstance(command, Polyline):
        xs, ys = zip(*command.points)
        ax.plot(
            xs,
            ys,
            color=command.color,
            linewidth=command.width,
            solid_capstyle="round",
            solid_joinstyle="round",
        )
        return
    if isinstance(command, Polygon):
        ax.add_patch(
            MatplotlibPolygon(
                command.points,
                closed=True,
                fill=command.fill is not None,
                facecolor=command.fill or "none",
                edgecolor=command.color,
                linewidth=command.width,
                joinstyle="round",
            )
        )
        return
    if isinstance(command, Circle):
        ax.add_patch(
            MatplotlibCircle(
                command.center,
                command.radius,
                facecolor=command.fill or "none",
                edgecolor=command.color,
                linewidth=command.width,
            )
        )
        return
    if isinstance(command, Text):
        ax.text(
            *command.point,
            command.value,
            color=command.color,
            fontsize=command.size,
            ha=command.align,
            va=command.valign,
            family=command.font_family,
        )
        return
    raise TypeError(f"Unsupported scene command: {type(command)!r}")


def render_matplotlib(
    diagram: Diagram,
    *,
    ax=None,
    style: Style = DEFAULT_STYLE,
    options: RenderOptions | None = None,
    padding: float | None = None,
):
    """Render ``diagram`` and return its Matplotlib figure.

    Both this backend and :func:`render_svg` consume the same resolved scene,
    keeping symbols, title placement, bounds, and labels in parity.
    """
    resolved_options = options or RenderOptions()
    if padding is not None:
        resolved_options = RenderOptions(
            width=resolved_options.width,
            height=resolved_options.height,
            dpi=resolved_options.dpi,
            padding=padding,
            background=resolved_options.background,
            avoid_label_collisions=resolved_options.avoid_label_collisions,
        )
    scene = layout_scene(diagram, style=style, options=resolved_options)
    assert scene.bounds is not None
    own_figure = ax is None
    if own_figure:
        figure = Figure(figsize=figure_size(scene.bounds, resolved_options), dpi=resolved_options.dpi)
        FigureCanvasAgg(figure)
        ax = figure.add_subplot()
    else:
        figure = ax.figure
    if resolved_options.background is None:
        figure.patch.set_alpha(0)
        ax.set_facecolor("none")
    else:
        figure.patch.set_facecolor(resolved_options.background)
        ax.set_facecolor(resolved_options.background)
    for command in scene.commands:
        _draw_command(ax, command)
    ax.set_xlim(scene.bounds.x0, scene.bounds.x1)
    ax.set_ylim(scene.bounds.y0, scene.bounds.y1)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    if own_figure:
        figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    return figure
