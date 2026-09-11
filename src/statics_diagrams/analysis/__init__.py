"""Optional structural-analysis models, backends, and result rendering.

Install ``statics-diagrams[analysis]`` to use the default anaStruct backend.
"""
from .model import Member, MemberKind, Node, NodeLoad, StructuralModel, Support, SupportType, UniformLoad
from .renderer import diagram_from_model
from .results import AnalysisResults, DisplacementResult, InternalForceResult, ReactionResult
from .service import AnalysisError, AnalysisService

__all__ = [
    "AnalysisError", "AnalysisResults", "AnalysisService", "DisplacementResult", "InternalForceResult",
    "Member", "MemberKind", "Node", "NodeLoad", "ReactionResult", "StructuralModel", "Support",
    "SupportType", "UniformLoad", "diagram_from_model",
]
