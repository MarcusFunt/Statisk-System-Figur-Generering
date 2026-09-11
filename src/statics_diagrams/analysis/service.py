"""The sole analysis entrypoint consumed by the GUI and other clients."""
from __future__ import annotations

from typing import Protocol

from .model import StructuralModel
from .results import AnalysisResults


class AnalysisError(RuntimeError):
    """A model-validation or backend-solver failure suitable for display to users."""


class AnalysisBackend(Protocol):
    name: str

    def analyze(self, model: StructuralModel) -> AnalysisResults: ...


class AnalysisService:
    """Stable backend boundary; the GUI must never import a solver package directly."""

    def __init__(self, backend: AnalysisBackend | None = None) -> None:
        if backend is None:
            from .anastruct_adapter import AnaStructAdapter

            backend = AnaStructAdapter()
        self._backend = backend

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def analyze(self, model: StructuralModel) -> AnalysisResults:
        return self._backend.analyze(model)
