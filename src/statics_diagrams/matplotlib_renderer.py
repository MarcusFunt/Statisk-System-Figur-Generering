"""Matplotlib output for the shared statics-diagrams scene."""
from __future__ import annotations

from .layout import Circle, Line, Polygon, Polyline, Text, figure_size, layout_scene
from .model import Diagram
from .options import RenderOptions
from .style import DEFAULT_STYLE, Style


def _draw_command(ax,command) -> None:
    from matplotlib.patches import Circle as MCircle
    from matplotlib.patches import Polygon as MPolygon
    if isinstance(command,Line):
        line,=ax.plot([command.start[0],command.end[0]],[command.start[1],command.end[1]],color=command.paint.color,linewidth=command.paint.width,alpha=command.paint.opacity,solid_capstyle="round",solid_joinstyle="round")
        if command.paint.dash: line.set_dashes(command.paint.dash)
    elif isinstance(command,Polyline):
        xs,ys=zip(*command.points); line,=ax.plot(xs,ys,color=command.paint.color,linewidth=command.paint.width,alpha=command.paint.opacity,solid_capstyle="round",solid_joinstyle="round");
        if command.paint.dash: line.set_dashes(command.paint.dash)
    elif isinstance(command,Polygon):
        ax.add_patch(MPolygon(command.points,closed=True,fill=command.paint.fill is not None,facecolor=command.paint.fill or "none",edgecolor=command.paint.color,linewidth=command.paint.width,alpha=command.paint.opacity,joinstyle="round"))
    elif isinstance(command,Circle):
        ax.add_patch(MCircle(command.center,command.radius,facecolor=command.paint.fill or "none",edgecolor=command.paint.color,linewidth=command.paint.width,alpha=command.paint.opacity))
    elif isinstance(command,Text):
        lines=command.value.split("\n"); n=len(lines); top=command.bounds_box.y1; step=command.bounds_box.height/max(n,1)
        for i,line in enumerate(lines):
            ax.text(command.point[0],top-i*step,line,color=command.color,fontsize=command.size,ha=command.align,va="top",family=command.font_family,alpha=command.opacity,parse_math=False)
    else: raise TypeError(type(command))


def render_matplotlib(diagram: Diagram,*,ax=None,style: Style=DEFAULT_STYLE,options: RenderOptions|None=None,padding: float|None=None):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    resolved=options or RenderOptions()
    if padding is not None:
        resolved=RenderOptions(width=resolved.width,height=resolved.height,dpi=resolved.dpi,padding=padding,background=resolved.background,avoid_label_collisions=resolved.avoid_label_collisions,svg_id_prefix=resolved.svg_id_prefix)
    scene=layout_scene(diagram,style=style,options=resolved); assert scene.bounds is not None; own=ax is None
    if own:
        figure=Figure(figsize=figure_size(scene.bounds,resolved),dpi=resolved.dpi); FigureCanvasAgg(figure); ax=figure.add_subplot()
        if resolved.background is None: figure.patch.set_alpha(0)
        else: figure.patch.set_facecolor(resolved.background)
    else: figure=ax.figure
    ax.set_facecolor("none" if resolved.background is None else resolved.background)
    for group in scene.groups:
        for command in group.commands:_draw_command(ax,command)
    ax.set_xlim(scene.bounds.x0,scene.bounds.x1); ax.set_ylim(scene.bounds.y0,scene.bounds.y1); ax.set_aspect("equal",adjustable="box"); ax.axis("off")
    if own: figure.subplots_adjust(left=0,right=1,bottom=0,top=1)
    return figure
