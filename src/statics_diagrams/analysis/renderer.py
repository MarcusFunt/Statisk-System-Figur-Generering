"""Render a neutral structural model and optional solved results with statics-diagrams."""
from __future__ import annotations

from math import copysign

from ..model import Diagram, SupportKind
from .model import StructuralModel, SupportType
from .results import AnalysisResults


def _scale(model: StructuralModel) -> float:
    xs = [node.x for node in model.nodes.values()]
    ys = [node.y for node in model.nodes.values()]
    return max(max(xs) - min(xs), max(ys) - min(ys), 1.0) * 0.12


def _label(prefix: str, value: float) -> str:
    return f"{prefix} = {value:.4g}"


def diagram_from_model(model: StructuralModel, results: AnalysisResults | None = None) -> Diagram:
    """Create a publication-quality diagram from the editable model and solved data."""
    diagram = Diagram(title=model.title)
    visual_scale = _scale(model)
    for member in model.members.values():
        start, end = model.nodes[member.start_node], model.nodes[member.end_node]
        diagram.beam((start.x, start.y), (end.x, end.y), kind="bar" if member.kind.value == "truss" else "beam", label=member.label)
    support_kind = {
        SupportType.PINNED: SupportKind.PIN,
        SupportType.FIXED: SupportKind.FIXED,
        SupportType.ROLLER_X: SupportKind.ROLLER,
        SupportType.ROLLER_Y: SupportKind.ROLLER,
    }
    for support in model.supports.values():
        node = model.nodes[support.node_id]
        angle = 90.0 if support.kind is SupportType.ROLLER_X else 0.0
        diagram.support((node.x, node.y), support_kind[support.kind], angle=angle, label=support.label)
    for node_load in model.node_loads:
        node = model.nodes[node_load.node_id]
        if node_load.fx or node_load.fy:
            dominant = (node_load.fx, node_load.fy)
            diagram.force(at=(node.x, node.y), direction=dominant, length=visual_scale, label=node_load.label or _label("F", max(abs(node_load.fx), abs(node_load.fy))))
        if node_load.moment:
            diagram.moment((node.x, node.y), clockwise=node_load.moment < 0, radius=visual_scale * 0.35, label=node_load.label or _label("M", node_load.moment))
    for uniform_load in model.uniform_loads:
        member = model.members[uniform_load.member_id]
        start, end = model.nodes[member.start_node], model.nodes[member.end_node]
        direction = (0.0, copysign(1.0, uniform_load.q)) if uniform_load.direction == "y" else (copysign(1.0, uniform_load.q), 0.0)
        diagram.udl((start.x, start.y), (end.x, end.y), direction=direction, height=visual_scale, label=uniform_load.label or _label("q", uniform_load.q))
    if results is not None:
        for reaction in results.reactions:
            node = model.nodes[reaction.node_id]
            for prefix, value, direction in (("Rₓ", reaction.fx, (1.0, 0.0)), ("Rᵧ", reaction.fy, (0.0, 1.0))):
                if abs(value) > 1e-9:
                    diagram.reaction((node.x, node.y), (direction[0] * copysign(visual_scale, value), direction[1] * copysign(visual_scale, value)), label=_label(prefix, value))
            if abs(reaction.moment) > 1e-9:
                diagram.moment((node.x, node.y), clockwise=reaction.moment < 0, radius=visual_scale * 0.55, label=_label("Rₘ", reaction.moment), color="#226a9e")
        for member in model.members.values():
            force = results.force_for(member.id)
            if force is None:
                continue
            start, end = model.nodes[member.start_node], model.nodes[member.end_node]
            diagram.text(((start.x + end.x) / 2, (start.y + end.y) / 2 + visual_scale * 0.55), f"|M|max = {force.maximum_moment:.4g}")
    return diagram
