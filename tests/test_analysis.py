from __future__ import annotations

import pytest

pytest.importorskip("anastruct")

from statics_diagrams.analysis import (
    AnalysisResults,
    AnalysisService,
    Member,
    Node,
    StructuralModel,
    Support,
    SupportType,
    UniformLoad,
    diagram_from_model,
)


def _beam() -> StructuralModel:
    model = StructuralModel(title="UDL beam")
    model.add_node(Node("A", 0, 0))
    model.add_node(Node("B", 5, 0))
    model.add_member(Member("AB", "A", "B", ea=1_000_000_000, ei=1_000_000))
    model.set_support(Support("A", SupportType.PINNED))
    model.set_support(Support("B", SupportType.ROLLER_Y))
    model.add_uniform_load(UniformLoad("AB", -10))
    return model


def test_anastruct_adapter_returns_neutral_beam_results():
    results = AnalysisService().analyze(_beam())
    reactions = {reaction.node_id: reaction for reaction in results.reactions}
    assert results.backend == "anaStruct"
    assert reactions["A"].fy == pytest.approx(25)
    assert reactions["B"].fy == pytest.approx(25)
    force = results.force_for("AB")
    assert force is not None and force.maximum_moment == pytest.approx(31.25, rel=0.02)
    assert len(force.shear) == len(force.moment) == len(force.deflection)


def test_result_renderer_adds_reactions_and_member_summary():
    model = _beam()
    diagram = diagram_from_model(model, AnalysisService().analyze(model))
    assert len(diagram.beams) == 1
    assert len(diagram.reactions) == 2
    assert any("|M|max" in text.value for text in diagram.texts)


def test_model_rejects_disconnected_nodes_and_bad_references():
    model = StructuralModel()
    model.add_node(Node("A", 0, 0))
    model.add_node(Node("B", 1, 0))
    with pytest.raises(ValueError, match="Unknown node"):
        model.add_member(Member("AB", "A", "missing"))
    model.add_member(Member("AB", "A", "B"))
    model.add_node(Node("C", 2, 0))
    with pytest.raises(ValueError, match="not connected"):
        model.validate()


def test_service_accepts_a_future_backend_without_gui_or_model_changes():
    class FakeBackend:
        name = "fake"

        def analyze(self, model: StructuralModel) -> AnalysisResults:
            return AnalysisResults(warnings=(model.title,), backend=self.name)

    assert AnalysisService(FakeBackend()).analyze(_beam()).backend == "fake"
