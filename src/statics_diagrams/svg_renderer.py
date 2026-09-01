"""Standalone SVG output for the shared statics-diagrams scene."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from .layout import Circle, Line, Polygon, Polyline, Scene, Text, figure_size, layout_scene
from .model import Diagram
from .options import RenderOptions
from .style import DEFAULT_STYLE, Style


def _f(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


@dataclass
class SVGDocument:
    """A complete SVG document returned by :func:`render_svg`."""

    content: str

    def save(self, path: str | Path) -> Path:
        output = Path(path)
        output.write_text(self.content, encoding="utf-8")
        return output


class _Canvas:
    def __init__(self, scene: Scene, options: RenderOptions) -> None:
        assert scene.bounds is not None
        self.bounds = scene.bounds
        self.width_in, self.height_in = figure_size(scene.bounds, options)
        self.width = self.width_in * options.dpi
        self.height = self.height_in * options.dpi
        self.ppu_x = self.width / self.bounds.width
        self.ppu_y = self.height / self.bounds.height
        self.stroke_scale = options.dpi / 72.0

    def point(self, point: tuple[float, float]) -> tuple[float, float]:
        return (
            (point[0] - self.bounds.x0) * self.ppu_x,
            (self.bounds.y1 - point[1]) * self.ppu_y,
        )

    def width_px(self, width: float) -> float:
        return width * self.stroke_scale


def _command_svg(command, canvas: _Canvas) -> str:
    if isinstance(command, Line):
        ax, ay = canvas.point(command.start)
        bx, by = canvas.point(command.end)
        dash = f' stroke-dasharray="{" ".join(_f(value) for value in command.dash)}"' if command.dash else ""
        return (
            f'<path d="M {_f(ax)} {_f(ay)} L {_f(bx)} {_f(by)}" fill="none" '
            f'stroke="{command.color}" stroke-width="{_f(canvas.width_px(command.width))}" '
            f'stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
    if isinstance(command, Polyline):
        points = " ".join(f"{_f(x)} {_f(y)}" for x, y in map(canvas.point, command.points))
        return (
            f'<polyline points="{points}" fill="none" stroke="{command.color}" '
            f'stroke-width="{_f(canvas.width_px(command.width))}" stroke-linecap="round" '
            'stroke-linejoin="round"/>'
        )
    if isinstance(command, Polygon):
        points = " ".join(f"{_f(x)} {_f(y)}" for x, y in map(canvas.point, command.points))
        fill = command.fill or "none"
        return (
            f'<polygon points="{points}" fill="{fill}" stroke="{command.color}" '
            f'stroke-width="{_f(canvas.width_px(command.width))}" stroke-linejoin="round"/>'
        )
    if isinstance(command, Circle):
        x, y = canvas.point(command.center)
        radius = command.radius * (canvas.ppu_x + canvas.ppu_y) / 2
        return (
            f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(radius)}" fill="{command.fill or "none"}" '
            f'stroke="{command.color}" stroke-width="{_f(canvas.width_px(command.width))}"/>'
        )
    if isinstance(command, Text):
        x, y = canvas.point(command.point)
        anchor = {"left": "start", "center": "middle", "right": "end"}[command.align]
        baseline = {"top": "hanging", "center": "middle", "bottom": "auto"}[command.valign]
        return (
            f'<text x="{_f(x)}" y="{_f(y)}" fill="{command.color}" '
            f'font-family="{escape(command.font_family)}" '
            f'font-size="{_f(canvas.width_px(command.size))}" text-anchor="{anchor}" '
            f'dominant-baseline="{baseline}">{escape(command.value)}</text>'
        )
    raise TypeError(f"Unsupported scene command: {type(command)!r}")


def render_svg(
    diagram: Diagram,
    *,
    style: Style = DEFAULT_STYLE,
    options: RenderOptions | None = None,
    padding: float | None = None,
    pixels_per_unit: float | None = None,
) -> SVGDocument:
    """Return an editable, semantically grouped standalone SVG document.

    ``padding`` and ``pixels_per_unit`` are retained as compatibility aliases;
    prefer :class:`RenderOptions` for physical output control.
    """
    resolved_options = options or RenderOptions()
    if padding is not None or pixels_per_unit is not None:
        resolved_options = RenderOptions(
            width=resolved_options.width,
            height=resolved_options.height,
            dpi=pixels_per_unit or resolved_options.dpi,
            padding=padding if padding is not None else resolved_options.padding,
            background=resolved_options.background,
            avoid_label_collisions=resolved_options.avoid_label_collisions,
        )
    scene = layout_scene(diagram, style=style, options=resolved_options)
    canvas = _Canvas(scene, resolved_options)
    parts: list[str] = []
    if resolved_options.background is not None:
        parts.append(f'<rect width="100%" height="100%" fill="{escape(resolved_options.background)}"/>')

    current_group: tuple[str, int] | None = None
    for command in scene.commands:
        group = (command.element_kind, command.element_id)
        if group != current_group:
            if current_group is not None:
                parts.append("</g>")
            parts.append(f'<g id="{group[0]}-{group[1]}" data-kind="{group[0]}">')
            current_group = group
        parts.append(_command_svg(command, canvas))
    if current_group is not None:
        parts.append("</g>")

    accessible_title = escape(diagram.title or "Statics diagram")
    content = "\n".join(parts)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{_f(canvas.width_in)}in" height="{_f(canvas.height_in)}in" '
        f'viewBox="0 0 {_f(canvas.width)} {_f(canvas.height)}" role="img" aria-labelledby="diagram-title">'
        f'<title id="diagram-title">{accessible_title}</title>{content}</svg>\n'
    )
    return SVGDocument(svg)
