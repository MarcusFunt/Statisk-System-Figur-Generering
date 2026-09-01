from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass

from statics_diagrams import COLORBLIND_STYLE, PRINT_STYLE, Diagram, RenderOptions, SupportKind
from statics_diagrams.layout import layout_scene


def _normal(obj):
    if is_dataclass(obj):
        values = asdict(obj)
        if obj.__class__.__name__ == "Text":
            values.pop("bounds_box", None)
        return {k:_normal(v) for k,v in values.items()}
    if isinstance(obj,float): return round(obj,6)
    if isinstance(obj,(list,tuple)): return [_normal(x) for x in obj]
    return obj


def digest(diagram,style=COLORBLIND_STYLE):
    scene=layout_scene(diagram,style=style,options=RenderOptions(width=6,background="white",avoid_label_collisions=False))
    payload=[{"kind":g.element_kind,"id":g.element_id,"z":g.z_index,"commands":[_normal(c) for c in g.commands]} for g in scene.groups]
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def cases():
    return {
        "beam": Diagram().beam((0,0),(8,0),label="AB").support((0,0),"pin",label="A").support((8,0),"roller",label="B").force(at=(3,0),direction=(0,-1),length=1.5,label="P").udl((5,0),(8,0),direction=(0,-1),height=1,label="q"),
        "rotated_support": Diagram().beam((0,0),(4,2)).support((0,0),"fixed",fixed_side="left",angle=35),
        "moment": Diagram().moment((0,0),radius=2,label="M"),
        "dense": Diagram().beam((0,0),(2,2)).beam((2,2),(4,0)).beam((0,0),(4,0)).hinge((2,2),label="C").force(at=(2,2),direction=(0,-1),length=1.2,label="P"),
        "portal": Diagram().beam((0,0),(0,3)).beam((0,3),(5,3)).beam((5,3),(5,0)).support((0,0),SupportKind.FIXED).support((5,0),SupportKind.PIN).dimension((0,-1),(5,-1),"L"),
    }


EXPECTED = {
    "beam": "5243fb99841ead0f635e3f9e85e826bbdec854bf42c153128c70dbd2529cb332",
    "rotated_support": "ca8b680e9c1a294c593827af653de552d56464be819da707c5f71c9acda96798",
    "moment": "07116d2d1ea39a286b61420041217693cf8f53d51293f683da566250251ee767",
    "dense": "349f0747db6b8aeb4f77be06bfe7b32131cc8978ee57fd0c7f885350881400d2",
    "portal": "d3277e9a8cd77b5626d62ff53db3c71aa33c2942fee50c7392cec55654fad8b1",
}


def test_visual_scene_snapshots():
    actual={name:digest(d, PRINT_STYLE if name=="portal" else COLORBLIND_STYLE) for name,d in cases().items()}
    assert actual == EXPECTED
