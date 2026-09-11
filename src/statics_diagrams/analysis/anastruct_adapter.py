"""anaStruct implementation of the neutral analysis-backend boundary."""
from __future__ import annotations

from .model import MemberKind, StructuralModel, SupportType
from .results import AnalysisResults, DisplacementResult, InternalForceResult, ReactionResult
from .service import AnalysisError


class AnaStructAdapter:
    """Maps a :class:`StructuralModel` to anaStruct without exposing it to callers."""

    name = "anaStruct"

    def analyze(self, model: StructuralModel) -> AnalysisResults:
        warnings = model.validate()
        try:
            from anastruct import SystemElements
        except ImportError as exc:
            raise AnalysisError("Install the analysis extra: pip install 'statics-diagrams[analysis]'.") from exc

        system = SystemElements()
        node_ids: dict[str, int] = {}
        member_ids: dict[str, int] = {}
        try:
            for member in model.members.values():
                start, end = model.nodes[member.start_node], model.nodes[member.end_node]
                location = [[start.x, start.y], [end.x, end.y]]
                if member.kind is MemberKind.TRUSS:
                    element_id = system.add_truss_element(location=location, EA=member.ea)
                else:
                    element_id = system.add_element(location=location, EA=member.ea, EI=member.ei)
                element = system.element_map[element_id]
                node_ids[member.start_node] = element.node_id1
                node_ids[member.end_node] = element.node_id2
                member_ids[member.id] = element_id

            for support in model.supports.values():
                node_id = node_ids[support.node_id]
                if support.kind is SupportType.PINNED:
                    system.add_support_hinged(node_id=node_id)
                elif support.kind is SupportType.FIXED:
                    system.add_support_fixed(node_id=node_id)
                elif support.kind is SupportType.ROLLER_X:
                    system.add_support_roll(node_id=node_id, direction=1)
                else:
                    system.add_support_roll(node_id=node_id, direction=2)

            for node_load in model.node_loads:
                system.point_load(node_id=node_ids[node_load.node_id], Fx=node_load.fx, Fy=node_load.fy, rotation=node_load.moment)
            for uniform_load in model.uniform_loads:
                system.q_load(q=uniform_load.q, element_id=member_ids[uniform_load.member_id], direction=uniform_load.direction)
            system.solve()
        except Exception as exc:
            raise AnalysisError(f"anaStruct could not solve this model: {exc}") from exc

        reactions: list[ReactionResult] = []
        displacements: list[DisplacementResult] = []
        for external_id, ana_id in node_ids.items():
            node = system.node_map[ana_id]
            displacements.append(DisplacementResult(external_id, float(node.ux), float(node.uy), float(node.phi_z)))
            if external_id in model.supports:
                reactions.append(ReactionResult(external_id, float(node.Fx), float(node.Fy), float(node.Tz)))

        member_forces: list[InternalForceResult] = []
        for external_id, ana_id in member_ids.items():
            element = system.element_map[ana_id]
            member_forces.append(InternalForceResult(
                external_id,
                tuple(float(value) for value in element.axial_force),
                tuple(float(value) for value in element.shear_force),
                tuple(float(value) for value in element.bending_moment),
                tuple(float(value) for value in element.total_deflection),
            ))
        return AnalysisResults(tuple(reactions), tuple(displacements), tuple(member_forces), warnings, self.name)
