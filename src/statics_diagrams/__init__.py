"""Analysis-free, stanli-inspired statics diagram rendering."""

from .matplotlib_renderer import render_matplotlib
from .model import Diagram, SupportKind
from .options import RenderOptions
from .style import COLORBLIND_STYLE, MONOCHROME_STYLE, PRINT_STYLE, THEMES, Style
from .svg_renderer import render_svg

__all__ = [
    "COLORBLIND_STYLE",
    "Diagram",
    "MONOCHROME_STYLE",
    "PRINT_STYLE",
    "RenderOptions",
    "Style",
    "SupportKind",
    "THEMES",
    "render_matplotlib",
    "render_svg",
]
