"""Semantic drawing primitives; this module intentionally contains no solver."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import hypot
from typing import Literal

Point = tuple[float, float]
Vector = tuple[float, float]
LabelPosition = Literal["auto", "above", "below", "left", "right", "center"]


class SupportKind(str, Enum):
    PIN = "pin"
    ROLLER = "roller"
    FIXED = "fixed"
    SPRING = "spring"


@dataclass(frozen=True)
class Beam:
    start: Point
    end: Point
    kind: Literal["beam", "bar"] = "beam"
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Support:
    point: Point
    kind: SupportKind
    angle: float = 0.0
    fixed_side: Literal["left", "right", "top", "bottom"] = "bottom"
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Hinge:
    point: Point
    radius: float | None = None
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class PointLoad:
    point: Point
    vector: Vector
    label: str | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class DistributedLoad:
    start: Point
    end: Point
    direction: Vector = (0.0, -1.0)
    label: str | None = None
    count: int = 7
    offset: float | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Moment:
    point: Point
    clockwise: bool = False
    label: str | None = None
    radius: float | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Reaction:
    point: Point
    vector: Vector
    label: str | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Dimension:
    start: Point
    end: Point
    label: str
    offset: float = 0.0
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None


@dataclass(frozen=True)
class Text:
    point: Point
    value: str
    align: Literal["left", "center", "right"] = "center"
    valign: Literal["top", "center", "bottom"] = "bottom"


@dataclass
class Diagram:
    """An ordered scene graph for a statics drawing.

    Methods return ``self`` so diagrams can be built fluently. Coordinates are
    drawing-space coordinates; the diagram never calculates reactions or force
    values.
    """

    title: str | None = None
    symbol_scale: float | None = None
    beams: list[Beam] = field(default_factory=list)
    supports: list[Support] = field(default_factory=list)
    hinges: list[Hinge] = field(default_factory=list)
    point_loads: list[PointLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)
    moments: list[Moment] = field(default_factory=list)
    reactions: list[Reaction] = field(default_factory=list)
    dimensions: list[Dimension] = field(default_factory=list)
    texts: list[Text] = field(default_factory=list)

    def beam(
        self,
        start: Point,
        end: Point,
        *,
        kind: Literal["beam", "bar"] = "beam",
        label: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        self.beams.append(Beam(start, end, kind, label, label_position, label_offset))
        return self

    def support(
        self,
        point: Point,
        kind: SupportKind | str,
        *,
        angle: float = 0.0,
        fixed_side: Literal["left", "right", "top", "bottom"] = "bottom",
        label: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        self.supports.append(
            Support(point, SupportKind(kind), angle, fixed_side, label, label_position, label_offset)
        )
        return self

    def hinge(
        self,
        point: Point,
        *,
        radius: float | None = None,
        label: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        self.hinges.append(Hinge(point, radius, label, label_position, label_offset))
        return self

    def point_load(
        self,
        point: Point,
        vector: Vector,
        *,
        label: str | None = None,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        unit(vector)
        self.point_loads.append(PointLoad(point, vector, label, color, label_position, label_offset))
        return self

    def force(
        self,
        *,
        at: Point,
        direction: Vector,
        length: float,
        label: str | None = None,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        """Add a point force whose arrowhead lands at its application point.

        ``direction`` denotes the physical arrow direction and ``length`` is a
        drawing length. This is the semantic alternative to ``point_load``,
        which deliberately remains a low-level tail-plus-vector primitive.
        """
        if length <= 0:
            raise ValueError("length must be positive.")
        direction_unit = unit(direction)
        vector = mul(direction_unit, length)
        start = add(at, mul(vector, -1))
        return self.point_load(
            start,
            vector,
            label=label,
            color=color,
            label_position=label_position,
            label_offset=label_offset,
        )

    def distributed_load(
        self,
        start: Point,
        end: Point,
        *,
        direction: Vector = (0, -1),
        label: str | None = None,
        count: int = 7,
        offset: float | None = None,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        if count < 2:
            raise ValueError("A distributed load needs at least two arrows.")
        unit(direction)
        if offset is not None and offset <= 0:
            raise ValueError("offset must be positive when provided.")
        self.distributed_loads.append(DistributedLoad(start, end, direction, label, count, offset, color, label_position, label_offset))
        return self

    def udl(
        self,
        start: Point,
        end: Point,
        *,
        direction: Vector,
        height: float,
        label: str | None = None,
        count: int = 7,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        """Add a uniformly distributed load with an explicit drawn height."""
        if height <= 0:
            raise ValueError("height must be positive.")
        return self.distributed_load(
            start,
            end,
            direction=direction,
            label=label,
            count=count,
            offset=height,
            color=color,
            label_position=label_position,
            label_offset=label_offset,
        )

    def moment(
        self,
        point: Point,
        *,
        clockwise: bool = False,
        label: str | None = None,
        radius: float | None = None,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        if radius is not None and radius <= 0:
            raise ValueError("radius must be positive when provided.")
        self.moments.append(Moment(point, clockwise, label, radius, color, label_position, label_offset))
        return self

    def reaction(
        self,
        point: Point,
        vector: Vector,
        *,
        label: str | None = None,
        color: str | None = None,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        unit(vector)
        self.reactions.append(Reaction(point, vector, label, color, label_position, label_offset))
        return self

    def dimension(
        self,
        start: Point,
        end: Point,
        label: str,
        *,
        offset: float = 0.0,
        label_position: LabelPosition = "auto",
        label_offset: Vector | None = None,
    ) -> Diagram:
        if start == end:
            raise ValueError("A dimension needs two distinct points.")
        self.dimensions.append(Dimension(start, end, label, offset, label_position, label_offset))
        return self

    def text(
        self,
        point: Point,
        value: str,
        *,
        align: Literal["left", "center", "right"] = "center",
        valign: Literal["top", "center", "bottom"] = "bottom",
    ) -> Diagram:
        self.texts.append(Text(point, value, align, valign))
        return self

    def extent(self) -> tuple[float, float, float, float]:
        points: list[Point] = []
        for beam in self.beams:
            points += [beam.start, beam.end]
        for support in self.supports:
            points.append(support.point)
        for hinge in self.hinges:
            points.append(hinge.point)
        for load in self.point_loads:
            points += [load.point, (load.point[0] + load.vector[0], load.point[1] + load.vector[1])]
        for load in self.distributed_loads:
            points += [load.start, load.end]
        for reaction in self.reactions:
            points += [
                reaction.point,
                (
                    reaction.point[0] + reaction.vector[0],
                    reaction.point[1] + reaction.vector[1],
                ),
            ]
        for moment in self.moments:
            radius = moment.radius or 0.0
            points += [
                (moment.point[0] - radius, moment.point[1] - radius),
                (moment.point[0] + radius, moment.point[1] + radius),
            ]
        for dimension in self.dimensions:
            points += [dimension.start, dimension.end]
        for text in self.texts:
            points.append(text.point)
        if not points:
            return (-1, 1, -1, 1)
        xs, ys = zip(*points)
        return min(xs), max(xs), min(ys), max(ys)

    def scale(self) -> float:
        if self.symbol_scale is not None:
            return self.symbol_scale
        x0, x1, y0, y1 = self.extent()
        span = max(x1 - x0, y1 - y0, 1.0)
        return span * 0.035


def unit(vector: Vector) -> Vector:
    length = hypot(*vector)
    if length == 0:
        raise ValueError("A direction vector cannot be zero.")
    return vector[0] / length, vector[1] / length


def normal(vector: Vector) -> Vector:
    x, y = unit(vector)
    return -y, x


def add(a: Point, b: Vector) -> Point:
    return a[0] + b[0], a[1] + b[1]


def mul(vector: Vector, amount: float) -> Vector:
    return vector[0] * amount, vector[1] * amount
