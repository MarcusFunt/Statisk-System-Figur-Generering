from __future__ import annotations

import math
import re
import subprocess
import sys
from xml.etree import ElementTree

import pytest

from statics_diagrams import (
    DEFAULT_STYLE,
    Diagram,
    ElementStyle,
    RenderOptions,
    Style,
    SupportKind,
    render_matplotlib,
    render_svg,
)
from statics_diagrams.layout import Circle, Line, Polygon, Text, layout_scene
from statics_diagrams.svg_renderer import _Canvas


def _ids(svg: str) -> list[str]:
    return re.findall(r'\bid="([^"]+)"', svg)


def test_insertion_order_is_default_and_z_index_is_explicit():
    d=Diagram().force(at=(1,0),direction=(0,-1),length=1).beam((0,0),(2,0))
    s=layout_scene(d,style=DEFAULT_STYLE,options=RenderOptions())
    assert [g.element_kind for g in s.groups[:2]]==["point-load","beam"]
    d2=Diagram().force(at=(1,0),direction=(0,-1),length=1,z_index=5).beam((0,0),(2,0),z_index=0)
    s2=layout_scene(d2,style=DEFAULT_STYLE,options=RenderOptions())
    assert [g.element_kind for g in s2.groups[:2]]==["beam","point-load"]


def test_svg_ids_unique_and_prefixable():
    d=Diagram(title="x").beam((0,0),(2,0),label="AB").support((0,0),"pin",label="A")
    svg=render_svg(d,options=RenderOptions(svg_id_prefix="fig1")).content
    ids=_ids(svg)
    assert len(ids)==len(set(ids))
    assert "fig1-diagram-title" in ids and "fig1-beam-0" in ids
    root=ElementTree.fromstring(svg); assert root.attrib["aria-labelledby"]=="fig1-diagram-title"


def test_text_metrics_distinguish_equal_length_glyphs():
    a=layout_scene(Diagram().text((0,0),"IIII"),style=DEFAULT_STYLE,options=RenderOptions())
    b=layout_scene(Diagram().text((0,0),"WWWW"),style=DEFAULT_STYLE,options=RenderOptions())
    ta=next(c for c in a.commands if isinstance(c,Text)); tb=next(c for c in b.commands if isinstance(c,Text))
    assert tb.bounds_box.width > ta.bounds_box.width


def test_multiline_svg_and_bounds():
    d=Diagram(title="A\nB").text((0,0),"line 1\nline 2")
    scene=layout_scene(d,style=DEFAULT_STYLE,options=RenderOptions())
    text=next(c for c in scene.commands if isinstance(c,Text) and c.value.startswith("line"))
    one=layout_scene(Diagram().text((0,0),"line 1"),style=DEFAULT_STYLE,options=RenderOptions())
    one_text=next(c for c in one.commands if isinstance(c,Text))
    assert text.bounds_box.height > one_text.bounds_box.height
    svg=render_svg(d).content
    assert svg.count("<tspan")>=4


def test_mathtext_is_literal_in_matplotlib():
    fig=render_matplotlib(Diagram().text((0,0),r"$F_x$"))
    assert fig.axes[0].texts[0].get_text()==r"$F_x$"
    assert getattr(fig.axes[0].texts[0],"_parse_math",False) is False


def test_symbol_scale_is_physically_stable():
    a=layout_scene(Diagram().beam((0,0),(10,0)).support((0,0),"pin"),style=DEFAULT_STYLE,options=RenderOptions(width=6))
    b=layout_scene(Diagram().beam((0,0),(100,0)).support((0,0),"pin"),style=DEFAULT_STYLE,options=RenderOptions(width=6))
    # world scale grows with span so rendered physical size remains stable
    assert b.scale/a.scale == pytest.approx(10,rel=.05)


def test_svg_canvas_uses_uniform_scale_with_forced_aspect():
    scene=layout_scene(Diagram().beam((0,0),(10,0)),style=DEFAULT_STYLE,options=RenderOptions(width=4,height=4))
    canvas=_Canvas(scene,RenderOptions(width=4,height=4))
    assert canvas.ppu>0
    # circle radius and coordinate distances use the same PPU
    x0,_=canvas.point((0,0)); x1,_=canvas.point((1,0)); assert x1-x0==pytest.approx(canvas.ppu)


def test_transparent_hinge_has_no_white_fill_and_clips_beam():
    d=Diagram().beam((0,0),(4,0)).hinge((2,0))
    scene=layout_scene(d,style=DEFAULT_STYLE,options=RenderOptions(background=None))
    beam=next(g for g in scene.groups if g.element_kind=="beam")
    hinge=next(g for g in scene.groups if g.element_kind=="hinge")
    assert len([c for c in beam.commands if isinstance(c,Line)])==2
    circle=next(c for c in hinge.commands if isinstance(c,Circle)); assert circle.paint.fill is None
    assert 'fill="white"' not in render_svg(d,options=RenderOptions(background=None)).content


def test_custom_background_propagates_to_knockout_fills():
    scene=layout_scene(Diagram().beam((0,0),(2,0)).hinge((1,0)).support((2,0),"roller"),style=DEFAULT_STYLE,options=RenderOptions(background="#eee"))
    circles=[c for c in scene.commands if isinstance(c,Circle)]
    assert circles and all(c.paint.fill=="#eee" for c in circles)


def test_fixed_support_wall_contains_hatch_roots():
    s=layout_scene(Diagram().support((0,0),"fixed",fixed_side="bottom"),style=DEFAULT_STYLE,options=RenderOptions())
    g=next(g for g in s.groups if g.element_kind=="support")
    lines=[c for c in g.commands if isinstance(c,Line)]
    wall=max(lines,key=lambda line: math.hypot(line.end[0]-line.start[0],line.end[1]-line.start[1]))
    lo,hi=sorted((wall.start[0],wall.end[0]))
    for hatch in lines:
        if hatch is wall: continue
        assert lo-1e-9 <= hatch.start[0] <= hi+1e-9


@pytest.mark.parametrize("factory",[
    lambda: Diagram().beam((0,0),(0,0)),
    lambda: Diagram().distributed_load((0,0),(0,0)),
    lambda: Diagram().hinge((0,0),radius=-1),
    lambda: Diagram(symbol_scale=0),
    lambda: Diagram().beam((0,0),(1,0),kind="wat"),
    lambda: Diagram().text((0,0),"x",align="wat"),
])
def test_invalid_geometry_is_rejected_early(factory):
    with pytest.raises(ValueError): factory()


@pytest.mark.parametrize("factory",[
    lambda: RenderOptions(width=float("nan")),
    lambda: RenderOptions(dpi=float("inf")),
    lambda: Diagram(symbol_scale=float("nan")),
    lambda: Diagram().force(at=(0,0),direction=(0,-1),length=float("nan")),
    lambda: Diagram().beam((0,0),(float("inf"),0)),
    lambda: Diagram().reaction((0,0),(float("inf"),0)),
])
def test_nonfinite_values_are_rejected(factory):
    with pytest.raises(ValueError): factory()


@pytest.mark.parametrize("factory",[
    lambda: Style(beam_width=-1),
    lambda: Style(text_size=0),
    lambda: Style(arrow_head_scale=float("nan")),
    lambda: Style(beam_dash=()),
    lambda: Style(beam_dash=(5,-2)),
])
def test_invalid_style_values_are_rejected(factory):
    with pytest.raises(ValueError): factory()


def test_pixels_per_unit_preserves_legacy_world_scale():
    d=Diagram().beam((0,0),(10,0))
    scene=layout_scene(d,style=DEFAULT_STYLE,options=RenderOptions())
    svg=render_svg(d,pixels_per_unit=50).content
    root=ElementTree.fromstring(svg); vb=[float(x) for x in root.attrib["viewBox"].split()]
    assert vb[2] == pytest.approx(scene.bounds.width*50,rel=1e-4)


def test_external_axes_does_not_mutate_figure_patch():
    from matplotlib.figure import Figure
    fig=Figure(); ax=fig.add_subplot(121); other=fig.add_subplot(122); fig.patch.set_facecolor("pink"); before=fig.patch.get_facecolor(); other_before=other.get_facecolor()
    render_matplotlib(Diagram().beam((0,0),(1,0)),ax=ax,options=RenderOptions(background=None))
    assert fig.patch.get_facecolor()==before and other.get_facecolor()==other_before


def test_svg_dash_lengths_scale_with_dpi():
    style=Style(beam_dash=(5,3))
    a=render_svg(Diagram().beam((0,0),(2,0)),style=style,options=RenderOptions(dpi=72)).content
    b=render_svg(Diagram().beam((0,0),(2,0)),style=style,options=RenderOptions(dpi=144)).content
    da=re.search(r'stroke-dasharray="([^"]+)"',a).group(1); db=re.search(r'stroke-dasharray="([^"]+)"',b).group(1)
    assert [float(x) for x in db.split()] == pytest.approx([2*float(x) for x in da.split()])


def test_svg_attribute_values_are_escaped():
    svg=render_svg(Diagram().force(at=(0,0),direction=(0,-1),length=1,color='red" onload="evil')).content
    ElementTree.fromstring(svg)
    assert 'onload="evil"' not in svg


def test_svg_only_import_does_not_eagerly_import_matplotlib(tmp_path):
    code="import sys,statics_diagrams; print('matplotlib' in sys.modules)"
    out=subprocess.check_output([sys.executable,"-c",code],text=True).strip()
    assert out=="False"


def test_default_style_is_public():
    from statics_diagrams import DEFAULT_STYLE as public
    assert public is DEFAULT_STYLE


def test_dimensions_include_witness_lines_and_endpoint_styles():
    scene=layout_scene(Diagram().dimension((0,0),(4,0),"L",offset=1,endpoint_style="dot"),style=DEFAULT_STYLE,options=RenderOptions())
    g=next(g for g in scene.groups if g.element_kind=="dimension")
    assert len([c for c in g.commands if isinstance(c,Line)])>=3
    assert len([c for c in g.commands if isinstance(c,Circle)])==2


def test_udl_auto_spacing_and_manual_override():
    scene=layout_scene(Diagram().udl((0,0),(2,0),direction=(0,-1),height=1).udl((0,-2),(20,-2),direction=(0,-1),height=1),style=DEFAULT_STYLE,options=RenderOptions())
    groups=[g for g in scene.groups if g.element_kind=="distributed-load"]
    counts=[sum(isinstance(c,Polygon) for c in g.commands) for g in groups]
    assert counts[1]>counts[0]
    manual=layout_scene(Diagram().udl((0,0),(20,0),direction=(0,-1),height=1,count=3),style=DEFAULT_STYLE,options=RenderOptions())
    assert sum(isinstance(c,Polygon) for c in manual.commands)==3


def test_group_transform_rotates_geometry_and_vectors():
    d=Diagram()
    with d.group(translate=(3,2),rotate=90):
        d.beam((0,0),(2,0)).reaction((0,0),(1,0)).axes((0,0))
    beam=d.beams[0]; reaction=d.reactions[0]
    assert beam.start==pytest.approx((3,2)) and beam.end==pytest.approx((3,4))
    assert reaction.vector==pytest.approx((0,1))
    axes=next(e for e in d.elements if e.__class__.__name__=="CoordinateAxes")
    assert axes.x_vector==pytest.approx((0,1.5))


def test_per_element_style_and_class_are_emitted():
    d=Diagram().beam((0,0),(2,0),style=ElementStyle(color="#123456",line_width=4),css_class="highlight")
    svg=render_svg(d).content
    assert '#123456' in svg and 'stroke-width="8"' in svg and 'class="highlight"' in svg


def test_svg_text_bottom_anchor_uses_precomputed_block_top():
    scene=layout_scene(Diagram().text((0,0),"gyp",valign="bottom"),style=DEFAULT_STYLE,options=RenderOptions())
    t=next(c for c in scene.commands if isinstance(c,Text)); assert t.bounds_box.y0==pytest.approx(0)
    svg=render_svg(Diagram().text((0,0),"gyp",valign="bottom")).content
    assert 'dominant-baseline="hanging"' in svg


def test_short_arrow_head_stays_within_arrow_length():
    scene=layout_scene(Diagram(symbol_scale=1).point_load((0,0),(0.1,0)),style=DEFAULT_STYLE,options=RenderOptions())
    g=next(g for g in scene.groups if g.element_kind=="point-load"); poly=next(c for c in g.commands if isinstance(c,Polygon))
    xs=[p[0] for p in poly.points]
    assert min(xs)>=-1e-9 and max(xs)<=0.1+1e-9


def test_new_symbol_vocabulary_renders_semantic_groups():
    d=(Diagram().triangular_load((0,0),(3,0),direction=(0,-1),height=1).spring((0,-1),(2,-1)).link((0,-2),(2,-2))
       .support((3,0),SupportKind.GUIDED).axes((0,0)).section_marker((1,0),label="A").angle_dimension((0,0),0,45,1,"45°")
       .leader((2,0),(3,1),"joint").displacement((1,0),(0.5,0),label="δ").curved_member((0,0),2,0,90))
    kinds={g.element_kind for g in layout_scene(d,style=DEFAULT_STYLE,options=RenderOptions()).groups}
    assert {"distributed-load","spring","link","support","axes","section-marker","angle-dimension","leader","displacement","arc-member"} <= kinds
