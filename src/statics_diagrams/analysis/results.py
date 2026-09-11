"""Solver-independent result values returned by structural-analysis backends."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReactionResult:
    node_id: str
    fx: float
    fy: float
    moment: float


@dataclass(frozen=True)
class DisplacementResult:
    node_id: str
    x: float
    y: float
    rotation: float


@dataclass(frozen=True)
class InternalForceResult:
    member_id: str
    axial: tuple[float, ...]
    shear: tuple[float, ...]
    moment: tuple[float, ...]
    deflection: tuple[float, ...]

    @property
    def maximum_moment(self) -> float:
        return max((abs(value) for value in self.moment), default=0.0)


@dataclass(frozen=True)
class AnalysisResults:
    reactions: tuple[ReactionResult, ...] = ()
    displacements: tuple[DisplacementResult, ...] = ()
    member_forces: tuple[InternalForceResult, ...] = ()
    warnings: tuple[str, ...] = ()
    backend: str = ""

    def force_for(self, member_id: str) -> InternalForceResult | None:
        return next((result for result in self.member_forces if result.member_id == member_id), None)
