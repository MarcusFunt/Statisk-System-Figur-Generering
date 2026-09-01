from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass

from statics_diagrams import COLORBLIND_STYLE, Diagram, PRINT_STYLE, RenderOptions, SupportKind
from statics_diagrams.layout import layout_scene


def _normal(obj):
    if is_dataclass(obj): return {k:_normal(v) for k,v in asdict(obj).items()}
    if isinstance(obj,float): return round(obj,6)
    if isinstance(obj,(list,tuple)): return [_normal(x) for x in obj]
    return obj


def digest(diagram,style=COLORBLIND_STYLE):
    scene=layout_scene(diagram,style=style,options=RenderOptions(width=6,background="white"))
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
    "beam": "c37f9208dd4f34ec4d91401d338324acc93ebe3a63b6af30dc6dc58afffe6564",
    "rotated_support": "d560a98bade62c08d305716894336ad55b1bef7b26261d999354407787440fd6",
    "moment": "9b06a59e36214666f094fe0a375b37ea8b7f5d6f630cc281919d325b2f9f30fe",
    "dense": "80b9452773601d1982004d049cd6c540a01b9ecb4910a38a1f55634f3e5a3f98",
    "portal": "716127ed257ac42fdc2c088b3a6eb2894752da2b972b5c7c029165680db4dec9",
}


def test_visual_scene_snapshots():
    actual={name:digest(d, PRINT_STYLE if name=="portal" else COLORBLIND_STYLE) for name,d in cases().items()}
    assert actual == EXPECTED
