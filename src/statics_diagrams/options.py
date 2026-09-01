"""Output options shared by the Matplotlib and SVG renderers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderOptions:
    """Controls physical output without changing drawing coordinates.

    ``width`` and ``height`` are measured in inches. When one dimension is
    omitted it is derived from the laid-out diagram aspect ratio. SVG uses the
    same physical dimensions, making its default framing match Matplotlib.
    """

    width: float | None = 8.0
    height: float | None = None
    dpi: float = 144.0
    padding: float = 3.0
    background: str | None = None
    avoid_label_collisions: bool = True

    def __post_init__(self) -> None:
        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive when provided.")
        if self.height is not None and self.height <= 0:
            raise ValueError("height must be positive when provided.")
        if self.width is None and self.height is None:
            raise ValueError("Provide at least one of width or height.")
        if self.dpi <= 0:
            raise ValueError("dpi must be positive.")
        if self.padding < 0:
            raise ValueError("padding cannot be negative.")
