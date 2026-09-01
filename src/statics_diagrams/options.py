"""Output options shared by the Matplotlib and SVG renderers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from math import isfinite

_PREFIX_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class RenderOptions:
    """Controls physical output without changing drawing coordinates."""

    width: float | None = 8.0
    height: float | None = None
    dpi: float = 144.0
    padding: float = 3.0
    background: str | None = None
    avoid_label_collisions: bool = True
    svg_id_prefix: str | None = None

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            value = getattr(self, name)
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError(f"{name} must be finite and positive when provided.")
        if self.width is None and self.height is None:
            raise ValueError("Provide at least one of width or height.")
        if not isfinite(self.dpi) or self.dpi <= 0:
            raise ValueError("dpi must be finite and positive.")
        if not isfinite(self.padding) or self.padding < 0:
            raise ValueError("padding must be finite and non-negative.")
        if self.svg_id_prefix is not None and not _PREFIX_RE.fullmatch(self.svg_id_prefix):
            raise ValueError("svg_id_prefix must be a safe XML/CSS identifier prefix.")
