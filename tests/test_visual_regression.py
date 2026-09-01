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
    "beam": "2f07f517da21f45a2c66586fcd19279ef3140d7025ea0b4a8d165362f5560f53",
    "rotated_support": "d560a98bade62c08d305716894336ad55b1bef7b26261d999354407787440fd6",
    "moment": "eab4bb1d58e8373eb8b27e53e8de0cb9a2fc701a286b1eff6e65b1aabe2208da",
    "dense": "98d747e6097e3ac48c973626f23dc579fbd21700a9bdd39e69da5d1d702f8a70",
    "portal": "f05a2719d8afbf06280a24b054face6250c24d0df8c7685d40972dd43ecfaab4",
}


def test_visual_scene_snapshots():
    actual={name:digest(d, PRINT_STYLE if name=="portal" else COLORBLIND_STYLE) for name,d in cases().items()}
    assert actual == EXPECTED
