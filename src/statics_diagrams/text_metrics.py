"""Backend-neutral-ish text measurement with an optional high-fidelity Matplotlib path."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class TextMetrics:
    width_points: float
    height_points: float
    line_height_points: float


def _fallback_line_width(text: str, size: float) -> float:
    units = 0.0
    for ch in text or " ":
        if ch in "ilI|!.,:'`": units += 0.28
        elif ch in "MW@%#": units += 0.95
        elif unicodedata.east_asian_width(ch) in {"W", "F"}: units += 1.0
        elif ch.isspace(): units += 0.32
        else: units += 0.58
    return units * size


def measure_text(text: str, font_family: str, size: float, line_spacing: float = 1.2) -> TextMetrics:
    lines = text.split("\n") or [""]
    widths: list[float] = []
    line_height = size * 1.05
    try:
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextPath
        prop = FontProperties(family=font_family, size=size)
        for line in lines:
            if not line:
                widths.append(0.0)
                continue
            path = TextPath((0, 0), line, prop=prop, usetex=False)
            ext = path.get_extents()
            widths.append(max(float(ext.width), 0.0))
            if ext.height > 0:
                line_height = max(line_height, float(ext.height) * 1.22)
    except Exception:
        widths = [_fallback_line_width(line, size) for line in lines]
    height = line_height + max(0, len(lines)-1) * line_height * line_spacing
    return TextMetrics(max(widths, default=0.0), height, line_height * line_spacing)
