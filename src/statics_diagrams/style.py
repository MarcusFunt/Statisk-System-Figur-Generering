"""Shared visual defaults and named themes."""

from dataclasses import dataclass, replace


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
    background: str | None = "white"
    arrow_head_scale: float = 0.36
    label_scale: float = 0.62
    beam_dash: tuple[float, ...] | None = None
    load_dash: tuple[float, ...] | None = None
    dimension_dash: tuple[float, ...] | None = None


DEFAULT_STYLE = Style()
MONOCHROME_STYLE = replace(DEFAULT_STYLE, load="#17212b", reaction="#17212b", ground="#4d5760")
PRINT_STYLE = replace(DEFAULT_STYLE, ink="#111111", load="#333333", reaction="#555555", ground="#777777")
COLORBLIND_STYLE = replace(
    DEFAULT_STYLE,
    load="#d55e00",
    reaction="#0072b2",
    ground="#6c757d",
)

THEMES: dict[str, Style] = {
    "default": DEFAULT_STYLE,
    "monochrome": MONOCHROME_STYLE,
    "print": PRINT_STYLE,
    "colorblind": COLORBLIND_STYLE,
}
