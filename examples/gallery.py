"""Generate a small gallery of common statics-diagrams figures."""
from pathlib import Path

from statics_diagrams import (
    COLORBLIND_STYLE,
    PRINT_STYLE,
    Diagram,
    ElementStyle,
    RenderOptions,
    render_matplotlib,
    render_svg,
)

OUT = Path(__file__).with_name("output")
OUT.mkdir(exist_ok=True)
OPTIONS = RenderOptions(width=7, dpi=180, background="white")


def examples() -> dict[str, tuple[Diagram, object]]:
    simply_supported = (
        Diagram(title="Simply supported beam")
        .beam((0, 0), (8, 0), label="AB")
        .support((0, 0), "pin", label="A")
        .support((8, 0), "roller", label="B")
        .force(at=(3, 0), direction=(0, -1), length=1.5, label="P")
        .udl((4.5, 0), (7.5, 0), direction=(0, -1), height=1.0, label="q")
        .dimension((0, 0), (8, 0), "8 m", offset=-1.35, endpoint_style="arrow")
    )
    varying = (
        Diagram(title="Linearly varying load")
        .beam((0, 0), (7, 0))
        .support((0, 0), "fixed", fixed_side="left")
        .triangular_load((1, 0), (7, 0), direction=(0, -1), height=1.6, label="q(x)")
        .section_marker((4.5, 0), label="A")
        .axes((0.6, 0.6), x_length=1.0, y_length=1.0)
    )
    annotated_frame = Diagram(title="Styled frame")
    with annotated_frame.group(translate=(1, 0), rotate=8):
        annotated_frame.beam((0, 0), (0, 3), style=ElementStyle(color="#0057b8"), css_class="highlight")
        annotated_frame.beam((0, 3), (5, 3)).beam((5, 3), (5, 0))
        annotated_frame.support((0, 0), "fixed").support((5, 0), "pin")
        annotated_frame.leader((5, 3), (6, 4), "joint B")
        annotated_frame.angle_dimension((0, 0), 0, 8, 1.0, "8°")
    return {
        "simply_supported": (simply_supported, COLORBLIND_STYLE),
        "varying_load": (varying, COLORBLIND_STYLE),
        "annotated_frame": (annotated_frame, PRINT_STYLE),
    }


def main() -> None:
    for name, (diagram, style) in examples().items():
        fig = render_matplotlib(diagram, style=style, options=OPTIONS)
        fig.savefig(OUT / f"{name}.png", dpi=OPTIONS.dpi)
        render_svg(diagram, style=style, options=OPTIONS).save(OUT / f"{name}.svg")


if __name__ == "__main__":
    main()
