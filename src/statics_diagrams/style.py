"""Shared visual defaults for the available rendering backends."""

from dataclasses import dataclass


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


DEFAULT_STYLE = Style()
