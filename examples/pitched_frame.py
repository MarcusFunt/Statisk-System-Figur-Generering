"""A clean editable model of the 6 m × 2.5–4 m pitched frame reference drawing.

Run ``python examples/pitched_frame.py`` to save ``pitched_frame.svg``. With
the optional GUI installed, run ``python examples/pitched_frame.py --editor``
to continue editing the same neutral structural model interactively.
"""
from __future__ import annotations

from math import atan2, degrees, hypot
from pathlib import Path
from sys import argv

from statics_diagrams import Diagram, ElementStyle, RenderOptions, SupportKind, render_svg
from statics_diagrams.analysis import Member, Node, StructuralModel, Support, SupportType

SPAN = 6.0
LEFT_HEIGHT = 2.5
RIGHT_HEIGHT = 4.0
ROOF_RISE = RIGHT_HEIGHT - LEFT_HEIGHT
ROOF_LENGTH = hypot(SPAN, ROOF_RISE)
ROOF_ANGLE = degrees(atan2(ROOF_RISE, SPAN))


def pitched_frame_model() -> StructuralModel:
    """Return the editable frame model with conventional pin/roller supports."""
    model = StructuralModel(title="Pitched portal frame — geometric model")
    model.add_node(Node("A", 0.0, 0.0, "A"))
    model.add_node(Node("B", SPAN, 0.0, "B"))
    model.add_node(Node("C", 0.0, LEFT_HEIGHT, "C"))
    model.add_node(Node("D", SPAN, RIGHT_HEIGHT, "D"))
    model.add_member(Member("base", "A", "B", label="Base member"))
    model.add_member(Member("left-column", "A", "C", label="Left column"))
    model.add_member(Member("roof", "C", "D", label="Roof member"))
    model.add_member(Member("right-column", "B", "D", label="Right column"))
    model.set_support(Support("A", SupportType.PINNED, "Pin support"))
    model.set_support(Support("B", SupportType.ROLLER_Y, "Roller support"))
    return model


def pitched_frame_diagram() -> Diagram:
    """Render the model with uncluttered engineering dimensions and angle cues."""
    frame = Diagram(title="Pitched portal frame — geometric model")
    frame.beam((0, 0), (SPAN, 0), label="AB")
    frame.beam((0, 0), (0, LEFT_HEIGHT), label="AC")
    frame.beam((0, LEFT_HEIGHT), (SPAN, RIGHT_HEIGHT), label="CD")
    frame.beam((SPAN, 0), (SPAN, RIGHT_HEIGHT), label="BD")
    frame.support((0, 0), SupportKind.PIN, label="A")
    frame.support((SPAN, 0), SupportKind.ROLLER, label="B")

    dimension_style = ElementStyle(color="#52616c", line_width=1.0)
    frame.dimension((0, 0), (SPAN, 0), f"{SPAN:.2f} m", offset=-0.75, style=dimension_style)
    frame.dimension((0, 0), (0, LEFT_HEIGHT), f"{LEFT_HEIGHT:.2f} m", offset=0.72, style=dimension_style)
    frame.dimension((SPAN, 0), (SPAN, RIGHT_HEIGHT), f"{RIGHT_HEIGHT:.2f} m", offset=-0.72, style=dimension_style)
    frame.dimension((0, LEFT_HEIGHT), (SPAN, RIGHT_HEIGHT), f"{ROOF_LENGTH:.2f} m", offset=0.58, style=dimension_style)
    frame.angle_dimension((0, LEFT_HEIGHT), -90, ROOF_ANGLE, 0.70, f"{90 + ROOF_ANGLE:.0f}°", style=dimension_style)
    frame.angle_dimension((SPAN, RIGHT_HEIGHT), 180 + ROOF_ANGLE, 270, 0.62, f"{90 - ROOF_ANGLE:.0f}°", style=dimension_style)
    frame.text((SPAN / 2, -1.55), "All dimensions in metres", style=dimension_style)
    return frame


if __name__ == "__main__":
    model = pitched_frame_model()
    if "--editor" in argv:
        from statics_diagrams.gui import launch_editor

        raise SystemExit(launch_editor(model))
    output = Path("pitched_frame.svg")
    render_svg(pitched_frame_diagram(), options=RenderOptions(width=9, background="white")).save(output)
    print(output.resolve())
