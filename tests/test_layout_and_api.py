from __future__ import annotations

from xml.etree import ElementTree

import pytest

from statics_diagrams import (
    COLORBLIND_STYLE,
    MONOCHROME_STYLE,
    Diagram,
    RenderOptions,
    SupportKind,
    render_matplotlib,
    render_svg,
)
from statics_diagrams.layout import Text, layout_scene


def test_moment_only_svg_uses_bounds_that_contain_the_moment():
    svg=render_svg(Diagram().moment((10,10),radius=2)).content; root=ElementTree.fromstring(svg); view_box=[float(v) for v in root.attrib['viewBox'].split()]; polyline=root.find('.//{http://www.w3.org/2000/svg}polyline'); assert polyline is not None; coordinates=[float(v) for v in polyline.attrib['points'].split()]; assert view_box[2]>0 and view_box[3]>0; assert all(0<=x<=view_box[2] for x in coordinates[::2]); assert all(0<=y<=view_box[3] for y in coordinates[1::2])

def test_title_is_visible_and_accessibly_named_in_svg():
    svg=render_svg(Diagram(title='Portal frame').beam((0,0),(4,0))).content; assert '<title id="diagram-title">Portal frame</title>' in svg; assert '>Portal frame</text>' in svg

def test_fixed_support_rotation_changes_its_svg_geometry():
    upright=render_svg(Diagram().beam((0,0),(4,0)).support((0,0),SupportKind.FIXED,fixed_side='left')).content; rotated=render_svg(Diagram().beam((0,0),(4,0)).support((0,0),SupportKind.FIXED,fixed_side='left',angle=35)).content; assert upright!=rotated

def test_force_places_arrowhead_at_the_application_point():
    d=Diagram().force(at=(2,0),direction=(0,-1),length=3,label='P'); load=d.point_loads[0]; assert load.point==(2.0,3.0); assert load.vector==(0.0,-3.0); assert load.label_position=='auto'

def test_udl_uses_an_explicit_height_and_validates_direction():
    d=Diagram().udl((0,0),(4,0),direction=(0,-3),height=1.5); assert d.distributed_loads[0].offset==1.5
    with pytest.raises(ValueError,match='direction'): Diagram().force(at=(0,0),direction=(0,0),length=1)

def test_render_options_control_canvas_and_semantic_svg_groups():
    options=RenderOptions(width=5,background=None,avoid_label_collisions=True); svg=render_svg(Diagram(title='Load case').beam((0,0),(4,0)).force(at=(2,0),direction=(0,-1),length=1),options=options).content; assert 'width="5in"' in svg; assert '<rect width="100%"' not in svg; assert 'data-kind="point-load"' in svg; assert MONOCHROME_STYLE.load==MONOCHROME_STYLE.ink; assert COLORBLIND_STYLE.load!=COLORBLIND_STYLE.reaction

def test_label_position_and_scale_aware_figure_size_are_honored():
    d=Diagram().beam((0,0),(10,0),label='AB',label_position='above').force(at=(5,0),direction=(0,-1),length=2,label='P',label_position='right'); fig=render_matplotlib(d,options=RenderOptions(width=8)); assert fig.get_size_inches()[0]==pytest.approx(8); assert fig.get_size_inches()[1]<4

def test_automatic_labels_use_a_clear_candidate_when_a_load_occupies_a_joint():
    d=Diagram().beam((0,0),(3,2)).beam((3,2),(6,0)).hinge((3,2),label='C').force(at=(3,2),direction=(0,-1),length=1.5); scene=layout_scene(d,style=COLORBLIND_STYLE,options=RenderOptions(width=6)); label=next(c for c in scene.commands if isinstance(c,Text) and c.value=='C'); assert label.point[0]>3
