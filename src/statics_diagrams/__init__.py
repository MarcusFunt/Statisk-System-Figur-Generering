"""Analysis-free, stanli-inspired statics diagram rendering."""

from .matplotlib_renderer import render_matplotlib
from .model import Diagram, SupportKind
from .style import Style
from .svg_renderer import render_svg

__all__ = ["Diagram", "Style", "SupportKind", "render_matplotlib", "render_svg"]
