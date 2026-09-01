"""Shared visual defaults, per-element overrides, and named themes."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite


def _positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")


def _dash(name: str, value: tuple[float, ...] | None) -> None:
    if value is None:
        return
    if not value:
        raise ValueError(f"{name} cannot be empty.")
    if any((not isfinite(v) or v < 0) for v in value) or not any(v > 0 for v in value):
        raise ValueError(f"{name} must contain finite non-negative lengths and at least one positive length.")


@dataclass(frozen=True)
class ElementStyle:
    """Optional per-element visual overrides. ``None`` inherits the global theme."""

    color: str | None = None
    line_width: float | None = None
    dash: tuple[float, ...] | None = None
    fill: str | None = None
    opacity: float | None = None

    def __post_init__(self) -> None:
        if self.line_width is not None:
            _positive("line_width", self.line_width)
        _dash("dash", self.dash)
        if self.opacity is not None and (not isfinite(self.opacity) or not 0 <= self.opacity <= 1):
            raise ValueError("opacity must be finite and between 0 and 1.")


@dataclass(frozen=True)
class Style:
    ink: str = "#17212b"
    load: str = "#d64b31"
    reaction: str = "#226a9e"
    ground: str = "#7a8792"
    dimension: str = "#52616c"
    beam_width: float = 2.8
    bar_width: float = 1.8
    force_width: float = 1.7
    text_size: float = 10.5
    font_family: str = "DejaVu Sans"
    background: str | None = "white"  # legacy symbol-fill default; canvas lives in RenderOptions
    arrow_head_scale: float = 0.36
    label_scale: float = 0.62
    distributed_load_spacing: float = 2.4
    line_spacing: float = 1.2
    beam_dash: tuple[float, ...] | None = None
    load_dash: tuple[float, ...] | None = None
    dimension_dash: tuple[float, ...] | None = None
    font_fallback: tuple[str, ...] = ("Arial", "sans-serif")
    load_label: str | None = "#9f3724"
    reaction_label: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "beam_width", "bar_width", "force_width", "text_size", "arrow_head_scale",
            "label_scale", "distributed_load_spacing", "line_spacing",
        ):
            _positive(name, getattr(self, name))
        _dash("beam_dash", self.beam_dash)
        _dash("load_dash", self.load_dash)
        _dash("dimension_dash", self.dimension_dash)
        if not self.font_family:
            raise ValueError("font_family cannot be empty.")
        if any(not fallback for fallback in self.font_fallback):
            raise ValueError("font_fallback entries cannot be empty.")


DEFAULT_STYLE = Style()
MONOCHROME_STYLE = replace(
    DEFAULT_STYLE,
    load="#17212b",
    reaction="#17212b",
    ground="#4d5760",
    dimension="#17212b",
    load_label="#17212b",
)
PRINT_STYLE = replace(
    DEFAULT_STYLE,
    ink="#111111",
    load="#333333",
    reaction="#555555",
    ground="#777777",
    dimension="#444444",
    load_label="#333333",
)
COLORBLIND_STYLE = replace(
    DEFAULT_STYLE,
    load="#d55e00",
    reaction="#0072b2",
    ground="#6c757d",
    load_label="#9b3f00",
)

THEMES: dict[str, Style] = {
    "default": DEFAULT_STYLE,
    "monochrome": MONOCHROME_STYLE,
    "print": PRINT_STYLE,
    "colorblind": COLORBLIND_STYLE,
}
