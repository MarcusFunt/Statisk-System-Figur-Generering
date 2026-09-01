"""Dependency-free standalone SVG output for the common scene."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from .layout import Circle, Line, Polygon, Polyline, Scene, Text, figure_size, layout_scene
from .model import Diagram
from .options import RenderOptions
from .style import DEFAULT_STYLE, Style


def _f(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _attr(value: str) -> str:
    return escape(value, quote=True)


@dataclass
class SVGDocument:
    content: str
    def save(self, path: str | Path) -> Path:
        output=Path(path); output.write_text(self.content,encoding="utf-8"); return output


class _Canvas:
    def __init__(self, scene: Scene, options: RenderOptions, pixels_per_unit: float | None=None) -> None:
        assert scene.bounds is not None
        self.bounds=scene.bounds; self.stroke_scale=options.dpi/72.0
        if pixels_per_unit is not None:
            if pixels_per_unit <= 0: raise ValueError("pixels_per_unit must be positive.")
            self.ppu=pixels_per_unit; self.width=self.bounds.width*self.ppu; self.height=self.bounds.height*self.ppu
            self.width_in=self.width/options.dpi; self.height_in=self.height/options.dpi; self.offset_x=0.0; self.offset_y=0.0
        else:
            self.width_in,self.height_in=figure_size(scene.bounds,options); self.width=self.width_in*options.dpi; self.height=self.height_in*options.dpi
            self.ppu=min(self.width/self.bounds.width,self.height/self.bounds.height)
            self.offset_x=(self.width-self.bounds.width*self.ppu)/2; self.offset_y=(self.height-self.bounds.height*self.ppu)/2
    def point(self,p: tuple[float,float]) -> tuple[float,float]:
        return self.offset_x+(p[0]-self.bounds.x0)*self.ppu, self.offset_y+(self.bounds.y1-p[1])*self.ppu
    def width_px(self,w: float) -> float:return w*self.stroke_scale


def _paint_attrs(paint,canvas: _Canvas,*,include_fill: bool=False) -> str:
    attrs=f'stroke="{_attr(paint.color)}" stroke-width="{_f(canvas.width_px(paint.width))}" opacity="{_f(paint.opacity)}"'
    if paint.dash: attrs+=f' stroke-dasharray="{" ".join(_f(canvas.width_px(v)) for v in paint.dash)}"'
    if include_fill: attrs+=f' fill="{_attr(paint.fill) if paint.fill is not None else "none"}"'
    return attrs


def _command_svg(command,canvas: _Canvas) -> str:
    if isinstance(command,Line):
        ax,ay=canvas.point(command.start); bx,by=canvas.point(command.end)
        return f'<path d="M {_f(ax)} {_f(ay)} L {_f(bx)} {_f(by)}" fill="none" {_paint_attrs(command.paint,canvas)} stroke-linecap="round" stroke-linejoin="round"/>'
    if isinstance(command,Polyline):
        pts=" ".join(f"{_f(x)} {_f(y)}" for x,y in map(canvas.point,command.points)); return f'<polyline points="{pts}" fill="none" {_paint_attrs(command.paint,canvas)} stroke-linecap="round" stroke-linejoin="round"/>'
    if isinstance(command,Polygon):
        pts=" ".join(f"{_f(x)} {_f(y)}" for x,y in map(canvas.point,command.points)); return f'<polygon points="{pts}" {_paint_attrs(command.paint,canvas,include_fill=True)} stroke-linejoin="round"/>'
    if isinstance(command,Circle):
        x,y=canvas.point(command.center); r=command.radius*canvas.ppu; return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" {_paint_attrs(command.paint,canvas,include_fill=True)}/>'
    if isinstance(command,Text):
        x,_=canvas.point(command.point); _,top_y=canvas.point((command.point[0],command.bounds_box.y1)); anchor={"left":"start","center":"middle","right":"end"}[command.align]; lines=command.value.split("\n"); size=canvas.width_px(command.size); line_step=size*command.line_spacing
        attrs=f'x="{_f(x)}" y="{_f(top_y)}" fill="{_attr(command.color)}" opacity="{_f(command.opacity)}" font-family="{_attr(command.font_family)}" font-size="{_f(size)}" text-anchor="{anchor}" dominant-baseline="hanging"'
        if len(lines)==1:return f'<text {attrs}>{escape(lines[0])}</text>'
        spans=[]
        for i,line in enumerate(lines): spans.append(f'<tspan x="{_f(x)}" dy="{_f(0 if i==0 else line_step)}">{escape(line)}</tspan>')
        return f'<text {attrs}>{"".join(spans)}</text>'
    raise TypeError(type(command))


def render_svg(diagram: Diagram,*,style: Style=DEFAULT_STYLE,options: RenderOptions|None=None,padding: float|None=None,pixels_per_unit: float|None=None) -> SVGDocument:
    resolved=options or RenderOptions()
    if padding is not None:
        resolved=RenderOptions(width=resolved.width,height=resolved.height,dpi=resolved.dpi,padding=padding,background=resolved.background,avoid_label_collisions=resolved.avoid_label_collisions,svg_id_prefix=resolved.svg_id_prefix)
    scene=layout_scene(diagram,style=style,options=resolved); canvas=_Canvas(scene,resolved,pixels_per_unit)
    prefix=f"{resolved.svg_id_prefix}-" if resolved.svg_id_prefix else ""; title_id=f"{prefix}diagram-title"; parts=[]
    if resolved.background is not None: parts.append(f'<rect width="100%" height="100%" fill="{_attr(resolved.background)}"/>')
    for group in scene.groups:
        gid=f"{prefix}{group.element_kind}-{group.element_id}"; cls=f' class="{_attr(group.css_class)}"' if group.css_class else ""
        parts.append(f'<g id="{_attr(gid)}" data-kind="{_attr(group.element_kind)}"{cls}>')
        parts.extend(_command_svg(c,canvas) for c in group.commands); parts.append("</g>")
    accessible=escape(diagram.title or "Statics diagram"); content="\n".join(parts)
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(canvas.width_in)}in" height="{_f(canvas.height_in)}in" viewBox="0 0 {_f(canvas.width)} {_f(canvas.height)}" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="{_attr(title_id)}">'
         f'<title id="{_attr(title_id)}">{accessible}</title>{content}</svg>\n')
    return SVGDocument(svg)
