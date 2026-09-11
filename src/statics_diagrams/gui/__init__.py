"""Optional PySide6 desktop editor for editable structural models.

Install ``statics-diagrams[gui]`` (or ``[app]`` for GUI plus anaStruct) before
calling :func:`launch_editor`.
"""
from __future__ import annotations

from ..analysis.model import StructuralModel
from ..analysis.service import AnalysisService


def launch_editor(model: StructuralModel | None = None, analysis_service: AnalysisService | None = None) -> int:
    """Start the interactive editor without making the core package depend on PySide6."""
    try:
        from .editor import run_editor
    except ImportError as exc:
        raise RuntimeError("Install the GUI extra: pip install 'statics-diagrams[gui]'.") from exc
    return run_editor(model=model, analysis_service=analysis_service)


__all__ = ["launch_editor"]
