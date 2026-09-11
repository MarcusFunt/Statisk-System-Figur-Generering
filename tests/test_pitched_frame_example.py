from __future__ import annotations

import importlib.util
from pathlib import Path
from xml.etree import ElementTree

import pytest

from statics_diagrams import render_svg


def _example_module():
    source = Path(__file__).parents[1] / "examples" / "pitched_frame.py"
    spec = importlib.util.spec_from_file_location("pitched_frame_example", source)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_pitched_frame_example_has_exact_geometry_and_renderable_dimensions():
    example = _example_module()
    model = example.pitched_frame_model()
    assert example.ROOF_LENGTH == pytest.approx(6.1846584384)
    assert example.ROOF_ANGLE == pytest.approx(14.0362434679)
    assert set(model.members) == {"base", "left-column", "roof", "right-column"}
    assert model.validate() == ("Model has no applied loads.",)
    svg = render_svg(example.pitched_frame_diagram()).content
    ElementTree.fromstring(svg)
    assert "6.18 m" in svg and "104°" in svg and "76°" in svg
