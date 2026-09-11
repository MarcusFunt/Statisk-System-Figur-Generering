"""Small interactive model editor. It communicates exclusively through AnalysisService."""
from __future__ import annotations

from math import hypot

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QAction, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..analysis.model import Member, Node, NodeLoad, StructuralModel, Support, SupportType
from ..analysis.renderer import diagram_from_model
from ..analysis.results import AnalysisResults, ReactionResult
from ..analysis.service import AnalysisError, AnalysisService
from ..options import RenderOptions
from ..svg_renderer import render_svg


class ModelView(QGraphicsView):
    def __init__(self, owner: EditorWindow) -> None:
        super().__init__()
        self.owner = owner
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def mousePressEvent(self, event) -> None:
        if event.button() is Qt.MouseButton.LeftButton and self.owner.tool_mode is not None:
            point = self.mapToScene(event.position().toPoint())
            self.owner.canvas_clicked(point.x(), -point.y())
            event.accept()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class EditorWindow(QMainWindow):
    """A deliberately small first editor: nodes, members, supports, loads, solve, export."""

    def __init__(self, model: StructuralModel | None = None, analysis_service: AnalysisService | None = None) -> None:
        super().__init__()
        self.model = model or StructuralModel(title="Untitled structural model")
        self.analysis_service = analysis_service or AnalysisService()
        self.results: AnalysisResults | None = None
        self.tool_mode: str | None = "node"
        self.pending_member_node: str | None = None
        self.selected_node_id: str | None = None
        self.scene = QGraphicsScene(self)
        self.view = ModelView(self)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        self.setWindowTitle("statics-diagrams editor")
        self.resize(1180, 760)
        self._create_toolbar()
        self._create_inspector()
        self._create_results_dock()
        self.refresh_scene(fit=True)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self)
        self.addToolBar(toolbar)
        for text, mode in (("Add node", "node"), ("Add member", "member"), ("Select", None)):
            action = QAction(text, self)
            action.triggered.connect(lambda checked=False, selected=mode: self._set_mode(selected))
            toolbar.addAction(action)
        toolbar.addSeparator()
        solve = QAction("Analyze", self)
        solve.triggered.connect(self.analyze)
        toolbar.addAction(solve)
        export = QAction("Export SVG", self)
        export.triggered.connect(self.export_svg)
        toolbar.addAction(export)

    def _create_inspector(self) -> None:
        dock = QDockWidget("Selected node", self)
        panel = QWidget(dock)
        layout = QVBoxLayout(panel)
        self.selected_label = QLabel("Click a node to select it.")
        layout.addWidget(self.selected_label)
        support_form = QFormLayout()
        self.support_kind = QComboBox()
        for kind in SupportType:
            self.support_kind.addItem(kind.value.replace("_", " "), kind)
        support_form.addRow("Support", self.support_kind)
        support_button = QPushButton("Set support")
        support_button.clicked.connect(self.set_support)
        support_form.addRow(support_button)
        layout.addLayout(support_form)
        load_form = QFormLayout()
        self.fx = self._spinbox()
        self.fy = self._spinbox()
        self.moment = self._spinbox()
        load_form.addRow("Fx", self.fx)
        load_form.addRow("Fy", self.fy)
        load_form.addRow("Moment", self.moment)
        load_button = QPushButton("Add nodal load")
        load_button.clicked.connect(self.add_nodal_load)
        load_form.addRow(load_button)
        layout.addLayout(load_form)
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_results_dock(self) -> None:
        dock = QDockWidget("Analysis results", self)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        dock.setWidget(self.result_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    @staticmethod
    def _spinbox() -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(-1_000_000_000, 1_000_000_000)
        box.setDecimals(4)
        box.setSingleStep(1.0)
        return box

    def _set_mode(self, mode: str | None) -> None:
        self.tool_mode = mode
        self.pending_member_node = None
        self.statusBar().showMessage("Pan/select" if mode is None else f"{mode.title()} tool active")

    def canvas_clicked(self, x: float, y: float) -> None:
        if self.tool_mode == "node":
            self._add_node(x, y)
        elif self.tool_mode == "member":
            node_id = self._nearest_node(x, y)
            if node_id is None:
                self.statusBar().showMessage("Click an existing node to make a member.")
                return
            if self.pending_member_node is None:
                self.pending_member_node = node_id
                self.selected_node_id = node_id
            elif node_id != self.pending_member_node:
                member_id = f"M{len(self.model.members) + 1}"
                self.model.add_member(Member(member_id, self.pending_member_node, node_id))
                self.pending_member_node = None
                self.results = None
            self._update_selected_label()
            self.refresh_scene()
        else:
            self.selected_node_id = self._nearest_node(x, y)
            self._update_selected_label()
            self.refresh_scene()

    def _add_node(self, x: float, y: float) -> None:
        snap = 0.5
        x, y = round(x / snap) * snap, round(y / snap) * snap
        if self._nearest_node(x, y, tolerance=0.01) is not None:
            return
        node_id = f"N{len(self.model.nodes) + 1}"
        self.model.add_node(Node(node_id, x, y, node_id))
        self.selected_node_id = node_id
        self.results = None
        self._update_selected_label()
        self.refresh_scene()

    def _nearest_node(self, x: float, y: float, tolerance: float | None = None) -> str | None:
        if not self.model.nodes:
            return None
        extent = max(
            max(node.x for node in self.model.nodes.values()) - min(node.x for node in self.model.nodes.values()),
            max(node.y for node in self.model.nodes.values()) - min(node.y for node in self.model.nodes.values()),
            1.0,
        )
        tolerance = tolerance if tolerance is not None else extent * 0.06
        node = min(self.model.nodes.values(), key=lambda item: hypot(item.x - x, item.y - y))
        return node.id if hypot(node.x - x, node.y - y) <= tolerance else None

    def set_support(self) -> None:
        if self.selected_node_id is None:
            return
        self.model.set_support(Support(self.selected_node_id, self.support_kind.currentData()))
        self.results = None
        self.refresh_scene()

    def add_nodal_load(self) -> None:
        if self.selected_node_id is None:
            return
        try:
            self.model.add_node_load(NodeLoad(self.selected_node_id, self.fx.value(), self.fy.value(), self.moment.value()))
        except ValueError as exc:
            self.statusBar().showMessage(str(exc))
            return
        self.results = None
        self.refresh_scene()

    def analyze(self) -> None:
        try:
            self.results = self.analysis_service.analyze(self.model)
        except (AnalysisError, ValueError) as exc:
            QMessageBox.warning(self, "Analysis failed", str(exc))
            return
        lines = [f"Backend: {self.results.backend}"]
        lines.extend(self.results.warnings)
        lines.extend(_reaction_line(reaction) for reaction in self.results.reactions)
        self.result_text.setPlainText("\n".join(lines))
        self.refresh_scene()

    def export_svg(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "structure.svg", "SVG files (*.svg)")
        if path:
            render_svg(diagram_from_model(self.model, self.results), options=RenderOptions(width=8)).save(path)

    def refresh_scene(self, *, fit: bool = False) -> None:
        self.scene.clear()
        pen = QPen(QColor("#17212b"), 0)
        reaction_pen = QPen(QColor("#226a9e"), 0)
        for member in self.model.members.values():
            start, end = self.model.nodes[member.start_node], self.model.nodes[member.end_node]
            self.scene.addItem(QGraphicsLineItem(start.x, -start.y, end.x, -end.y)).setPen(pen)
        for support in self.model.supports.values():
            node = self.model.nodes[support.node_id]
            marker = QGraphicsSimpleTextItem("▾" if support.kind is not SupportType.FIXED else "┃")
            marker.setPos(node.x - 0.1, -node.y + 0.05)
            self.scene.addItem(marker)
        for node in self.model.nodes.values():
            radius = 0.08
            item = QGraphicsEllipseItem(node.x - radius, -node.y - radius, radius * 2, radius * 2)
            item.setPen(QPen(QColor("#17212b"), 0))
            item.setBrush(QColor("#f8fafc") if node.id != self.selected_node_id else QColor("#f2c94c"))
            self.scene.addItem(item)
            label = QGraphicsSimpleTextItem(node.label or node.id)
            label.setPos(node.x + radius, -node.y - radius)
            self.scene.addItem(label)
        for load in self.model.node_loads:
            node = self.model.nodes[load.node_id]
            if load.fx or load.fy:
                length = 0.7
                norm = max(hypot(load.fx, load.fy), 1e-12)
                item = QGraphicsLineItem(node.x - load.fx / norm * length, -node.y + load.fy / norm * length, node.x, -node.y)
                item.setPen(QPen(QColor("#d64b31"), 0))
                self.scene.addItem(item)
        if self.results is not None:
            for reaction in self.results.reactions:
                node = self.model.nodes[reaction.node_id]
                for value, dx, dy in ((reaction.fx, 1, 0), (reaction.fy, 0, 1)):
                    if abs(value) > 1e-9:
                        sign = 1 if value > 0 else -1
                        item = QGraphicsLineItem(node.x, -node.y, node.x + dx * sign * 0.7, -node.y - dy * sign * 0.7)
                        item.setPen(reaction_pen)
                        self.scene.addItem(item)
        bounds = self.scene.itemsBoundingRect().adjusted(-1, -1, 1, 1) if self.scene.items() else QRectF(-5, -5, 10, 10)
        self.scene.setSceneRect(bounds)
        if fit:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _update_selected_label(self) -> None:
        if self.selected_node_id is None:
            self.selected_label.setText("Click a node to select it.")
        else:
            node = self.model.nodes[self.selected_node_id]
            self.selected_label.setText(f"{node.id}: ({node.x:g}, {node.y:g})")


def _reaction_line(reaction: ReactionResult) -> str:
    return f"{reaction.node_id}: Rx={reaction.fx:.4g}, Ry={reaction.fy:.4g}, M={reaction.moment:.4g}"


def run_editor(model: StructuralModel | None = None, analysis_service: AnalysisService | None = None) -> int:
    app = QApplication.instance() or QApplication([])
    window = EditorWindow(model=model, analysis_service=analysis_service)
    window.show()
    return app.exec()
