"""Publication-quality, analysis-free statics diagram rendering."""
from __future__ import annotations

from .model import Diagram, SupportKind
from .options import RenderOptions
from .style import COLORBLIND_STYLE, DEFAULT_STYLE, MONOCHROME_STYLE, PRINT_STYLE, THEMES, ElementStyle, Style
from .svg_renderer import render_svg


def render_matplotlib(*args, **kwargs):
    """Lazily import the optional Matplotlib backend."""
    try:
        from .matplotlib_renderer import render_matplotlib as _render
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("matplotlib"):
            raise ModuleNotFoundError("Matplotlib rendering requires `pip install statics-diagrams[matplotlib]`.") from exc
        raise
    return _render(*args, **kwargs)


__all__=["COLORBLIND_STYLE","DEFAULT_STYLE","Diagram","ElementStyle","MONOCHROME_STYLE","PRINT_STYLE","RenderOptions","Style","SupportKind","THEMES","render_matplotlib","render_svg"]
