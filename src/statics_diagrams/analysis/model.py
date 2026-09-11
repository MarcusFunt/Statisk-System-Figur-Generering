"""Backend-neutral 2D structural model used by the GUI and analysis services."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite


class MemberKind(str, Enum):
    FRAME = "frame"
    TRUSS = "truss"


class SupportType(str, Enum):
    PINNED = "pinned"
    FIXED = "fixed"
    ROLLER_X = "roller_x"
    ROLLER_Y = "roller_y"


@dataclass(frozen=True)
class Node:
    id: str
    x: float
    y: float
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Node id cannot be empty.")
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("Node coordinates must be finite.")


@dataclass(frozen=True)
class Member:
    id: str
    start_node: str
    end_node: str
    ea: float = 210_000_000.0
    ei: float = 8_400_000.0
    kind: MemberKind = MemberKind.FRAME
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Member id cannot be empty.")
        if self.start_node == self.end_node:
            raise ValueError("A member needs two different nodes.")
        if not isfinite(self.ea) or self.ea <= 0:
            raise ValueError("ea must be finite and positive.")
        if self.kind is MemberKind.FRAME and (not isfinite(self.ei) or self.ei <= 0):
            raise ValueError("ei must be finite and positive for a frame member.")


@dataclass(frozen=True)
class Support:
    node_id: str
    kind: SupportType
    label: str | None = None


@dataclass(frozen=True)
class NodeLoad:
    node_id: str
    fx: float = 0.0
    fy: float = 0.0
    moment: float = 0.0
    label: str | None = None

    def __post_init__(self) -> None:
        if not all(isfinite(value) for value in (self.fx, self.fy, self.moment)):
            raise ValueError("Nodal loads must be finite.")
        if self.fx == self.fy == self.moment == 0:
            raise ValueError("A nodal load needs a non-zero force or moment.")


@dataclass(frozen=True)
class UniformLoad:
    member_id: str
    q: float
    direction: str = "y"
    label: str | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.q) or self.q == 0:
            raise ValueError("Uniform load q must be finite and non-zero.")
        if self.direction not in {"x", "y", "element"}:
            raise ValueError("Uniform-load direction must be x, y, or element.")


@dataclass
class StructuralModel:
    """A small editable 2D model; no solver-specific data belongs here."""

    title: str = "Structural model"
    nodes: dict[str, Node] = field(default_factory=dict)
    members: dict[str, Member] = field(default_factory=dict)
    supports: dict[str, Support] = field(default_factory=dict)
    node_loads: list[NodeLoad] = field(default_factory=list)
    uniform_loads: list[UniformLoad] = field(default_factory=list)

    def add_node(self, node: Node) -> Node:
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id!r} already exists.")
        if any((node.x, node.y) == (other.x, other.y) for other in self.nodes.values()):
            raise ValueError("Nodes must not share the same coordinates.")
        self.nodes[node.id] = node
        return node

    def add_member(self, member: Member) -> Member:
        if member.id in self.members:
            raise ValueError(f"Member {member.id!r} already exists.")
        self._require_nodes(member.start_node, member.end_node)
        self.members[member.id] = member
        return member

    def set_support(self, support: Support) -> Support:
        self._require_nodes(support.node_id)
        self.supports[support.node_id] = support
        return support

    def add_node_load(self, load: NodeLoad) -> NodeLoad:
        self._require_nodes(load.node_id)
        self.node_loads.append(load)
        return load

    def add_uniform_load(self, load: UniformLoad) -> UniformLoad:
        if load.member_id not in self.members:
            raise ValueError(f"Unknown member {load.member_id!r}.")
        self.uniform_loads.append(load)
        return load

    def validate(self) -> tuple[str, ...]:
        if not self.nodes:
            raise ValueError("A structural model needs at least one node.")
        if not self.members:
            raise ValueError("A structural model needs at least one member.")
        connected = {node_id for member in self.members.values() for node_id in (member.start_node, member.end_node)}
        detached = sorted(set(self.nodes) - connected)
        if detached:
            raise ValueError(f"Nodes are not connected to any member: {', '.join(detached)}.")
        warnings: list[str] = []
        if not self.supports:
            warnings.append("Model has no supports and will be unstable.")
        if not self.node_loads and not self.uniform_loads:
            warnings.append("Model has no applied loads.")
        return tuple(warnings)

    def _require_nodes(self, *node_ids: str) -> None:
        missing = [node_id for node_id in node_ids if node_id not in self.nodes]
        if missing:
            raise ValueError(f"Unknown node(s): {', '.join(missing)}.")
