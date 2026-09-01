"""Analysis-free semantic drawing primitives."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from enum import Enum
from math import atan2, cos, hypot, isfinite, pi, sin
from typing import Literal, TypeAlias

from .geometry import Transform, add, finite_point, finite_scalar, finite_vector, mul, unit
from .style import ElementStyle

Point = tuple[float, float]
Vector = tuple[float, float]
LabelPosition = Literal["auto", "above", "below", "left", "right", "center"]
EndpointStyle = Literal["tick", "arrow", "slash", "dot", "none"]
_LABEL_POSITIONS = {"auto", "above", "below", "left", "right", "center"}
_ENDPOINT_STYLES = {"tick", "arrow", "slash", "dot", "none"}
_CSS_SAFE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. ")


def _label_position(value: str) -> LabelPosition:
    if value not in _LABEL_POSITIONS:
        raise ValueError(f"label_position must be one of {sorted(_LABEL_POSITIONS)}.")
    return value  # type: ignore[return-value]


def _css_class(value: str | None) -> str | None:
    if value is not None and (not value or any(ch not in _CSS_SAFE for ch in value)):
        raise ValueError("css_class may contain only letters, digits, spaces, underscore, dash, and dot.")
    return value


def _z(value: int) -> int:
    if not isinstance(value, int):
        raise ValueError("z_index must be an integer.")
    return value


class SupportKind(str, Enum):
    PIN = "pin"
    ROLLER = "roller"
    FIXED = "fixed"
    SPRING = "spring"
    GUIDED = "guided"
    SLIDER = "slider"


@dataclass(frozen=True)
class Beam:
    start: Point
    end: Point
    kind: Literal["beam", "bar"] = "beam"
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class ArcMember:
    center: Point
    radius: float
    start_angle: float
    end_angle: float
    kind: Literal["beam", "bar"] = "beam"
    label: str | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Support:
    point: Point
    kind: SupportKind
    angle: float = 0.0
    fixed_side: Literal["left", "right", "top", "bottom"] = "bottom"
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Hinge:
    point: Point
    radius: float | None = None
    label: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class PointLoad:
    point: Point
    vector: Vector
    label: str | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class DistributedLoad:
    start: Point
    end: Point
    direction: Vector = (0.0, -1.0)
    label: str | None = None
    count: int | None = None
    offset: float | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    start_height: float | None = None
    end_height: float | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Moment:
    point: Point
    clockwise: bool = False
    label: str | None = None
    radius: float | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Reaction:
    point: Point
    vector: Vector
    label: str | None = None
    color: str | None = None
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Dimension:
    start: Point
    end: Point
    label: str
    offset: float = 0.0
    label_position: LabelPosition = "auto"
    label_offset: Vector | None = None
    extension_lines: bool = True
    endpoint_style: EndpointStyle = "tick"
    extension_gap: float = 0.08
    extension_overrun: float = 0.12
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class AngleDimension:
    center: Point
    start_angle: float
    end_angle: float
    radius: float
    label: str
    clockwise: bool = False
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Text:
    point: Point
    value: str
    align: Literal["left", "center", "right"] = "center"
    valign: Literal["top", "center", "bottom"] = "bottom"
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Spring:
    start: Point
    end: Point
    label: str | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Link:
    start: Point
    end: Point
    label: str | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class CoordinateAxes:
    origin: Point
    x_vector: Vector = (1.5, 0.0)
    y_vector: Vector = (0.0, 1.5)
    x_label: str = "x"
    y_label: str = "y"
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class SectionMarker:
    point: Point
    direction: Vector = (0.0, 1.0)
    label: str | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Leader:
    target: Point
    text_point: Point
    text: str
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


@dataclass(frozen=True)
class Displacement:
    point: Point
    vector: Vector
    label: str | None = None
    style: ElementStyle | None = None
    css_class: str | None = None
    z_index: int = 0


DiagramElement: TypeAlias = (
    Beam | ArcMember | Support | Hinge | PointLoad | DistributedLoad | Moment | Reaction |
    Dimension | AngleDimension | Text | Spring | Link | CoordinateAxes | SectionMarker |
    Leader | Displacement
)


class Diagram:
    """Ordered semantic scene graph. Methods return ``self`` for fluent construction."""

    def __init__(self, title: str | None = None, symbol_scale: float | None = None) -> None:
        if symbol_scale is not None:
            symbol_scale = finite_scalar("symbol_scale", symbol_scale)
            if symbol_scale <= 0:
                raise ValueError("symbol_scale must be positive.")
        self.title = title
        self.symbol_scale = symbol_scale
        self.elements: list[DiagramElement] = []
        self._transform_stack: list[Transform] = [Transform()]

    @property
    def beams(self) -> list[Beam]: return [e for e in self.elements if isinstance(e, Beam)]
    @property
    def arc_members(self) -> list[ArcMember]: return [e for e in self.elements if isinstance(e, ArcMember)]
    @property
    def supports(self) -> list[Support]: return [e for e in self.elements if isinstance(e, Support)]
    @property
    def hinges(self) -> list[Hinge]: return [e for e in self.elements if isinstance(e, Hinge)]
    @property
    def point_loads(self) -> list[PointLoad]: return [e for e in self.elements if isinstance(e, PointLoad)]
    @property
    def distributed_loads(self) -> list[DistributedLoad]: return [e for e in self.elements if isinstance(e, DistributedLoad)]
    @property
    def moments(self) -> list[Moment]: return [e for e in self.elements if isinstance(e, Moment)]
    @property
    def reactions(self) -> list[Reaction]: return [e for e in self.elements if isinstance(e, Reaction)]
    @property
    def dimensions(self) -> list[Dimension]: return [e for e in self.elements if isinstance(e, Dimension)]
    @property
    def texts(self) -> list[Text]: return [e for e in self.elements if isinstance(e, Text)]

    def _t(self) -> Transform:
        return self._transform_stack[-1]

    def _common(self, label_position: str, label_offset: Vector | None, css_class: str | None, z_index: int) -> tuple[LabelPosition, Vector | None, str | None, int]:
        lp = _label_position(label_position)
        lo = self._t().vector(finite_vector("label_offset", label_offset)) if label_offset is not None else None
        return lp, lo, _css_class(css_class), _z(z_index)

    def beam(self, start: Point, end: Point, *, kind: Literal["beam", "bar"] = "beam", label: str | None = None,
             label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
             css_class: str | None = None, z_index: int = 0) -> Diagram:
        if kind not in {"beam", "bar"}: raise ValueError("kind must be 'beam' or 'bar'.")
        start, end = finite_point("start", start), finite_point("end", end)
        if start == end: raise ValueError("A beam needs two distinct points.")
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        self.elements.append(Beam(self._t().point(start), self._t().point(end), kind, label, lp, lo, style, cc, z))
        return self

    def curved_member(self, center: Point, radius: float, start_angle: float, end_angle: float, *, kind: Literal["beam", "bar"] = "beam",
                      label: str | None = None, style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        center = finite_point("center", center); radius = finite_scalar("radius", radius)
        if radius <= 0: raise ValueError("radius must be positive.")
        start_angle = finite_scalar("start_angle", start_angle); end_angle = finite_scalar("end_angle", end_angle)
        if start_angle == end_angle: raise ValueError("Curved member needs a non-zero angular span.")
        if kind not in {"beam", "bar"}: raise ValueError("kind must be 'beam' or 'bar'.")
        t = self._t(); scale = hypot(*t.vector((1, 0))); rot = atan2(t.c, t.a) * 180 / pi
        self.elements.append(ArcMember(t.point(center), radius * scale, start_angle + rot, end_angle + rot, kind, label, style, _css_class(css_class), _z(z_index)))
        return self

    def support(self, point: Point, kind: SupportKind | str, *, angle: float = 0.0,
                fixed_side: Literal["left", "right", "top", "bottom"] = "bottom", label: str | None = None,
                label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
                css_class: str | None = None, z_index: int = 0) -> Diagram:
        point = finite_point("point", point); angle = finite_scalar("angle", angle)
        try: kind = SupportKind(kind)
        except ValueError as exc: raise ValueError(f"Unknown support kind: {kind!r}") from exc
        if fixed_side not in {"left", "right", "top", "bottom"}: raise ValueError("fixed_side must be left/right/top/bottom.")
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        transformed_tangent = self._t().vector((cos(angle*pi/180), sin(angle*pi/180)))
        transformed_angle = atan2(transformed_tangent[1], transformed_tangent[0]) * 180 / pi
        self.elements.append(Support(self._t().point(point), kind, transformed_angle, fixed_side, label, lp, lo, style, cc, z))
        return self

    def hinge(self, point: Point, *, radius: float | None = None, label: str | None = None,
              label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
              css_class: str | None = None, z_index: int = 0) -> Diagram:
        point = finite_point("point", point)
        if radius is not None:
            radius = finite_scalar("radius", radius)
            if radius <= 0: raise ValueError("radius must be positive.")
            radius *= hypot(*self._t().vector((1, 0)))
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        self.elements.append(Hinge(self._t().point(point), radius, label, lp, lo, style, cc, z))
        return self

    def point_load(self, point: Point, vector: Vector, *, label: str | None = None, color: str | None = None,
                   label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
                   css_class: str | None = None, z_index: int = 0) -> Diagram:
        point = finite_point("point", point); vector = finite_vector("vector", vector, nonzero=True)
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        self.elements.append(PointLoad(self._t().point(point), self._t().vector(vector), label, color, lp, lo, style, cc, z))
        return self

    def force(self, *, at: Point, direction: Vector, length: float, label: str | None = None, color: str | None = None,
              label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
              css_class: str | None = None, z_index: int = 0) -> Diagram:
        at = finite_point("at", at); direction = finite_vector("direction", direction, nonzero=True); length = finite_scalar("length", length)
        if length <= 0: raise ValueError("length must be positive.")
        vector = mul(unit(direction), length); start = add(at, mul(vector, -1))
        return self.point_load(start, vector, label=label, color=color, label_position=label_position, label_offset=label_offset,
                               style=style, css_class=css_class, z_index=z_index)

    def distributed_load(self, start: Point, end: Point, *, direction: Vector = (0, -1), label: str | None = None,
                         count: int | None = None, offset: float | None = None, color: str | None = None,
                         label_position: LabelPosition = "auto", label_offset: Vector | None = None,
                         start_height: float | None = None, end_height: float | None = None,
                         style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        start = finite_point("start", start); end = finite_point("end", end)
        if start == end: raise ValueError("A distributed load needs two distinct points.")
        direction = finite_vector("direction", direction, nonzero=True)
        if count is not None and (not isinstance(count, int) or count < 2): raise ValueError("count must be None or an integer >= 2.")
        if offset is not None:
            offset = finite_scalar("offset", offset)
            if offset <= 0: raise ValueError("offset must be positive.")
        for name, value in (("start_height", start_height), ("end_height", end_height)):
            if value is not None and (not isfinite(value) or value < 0): raise ValueError(f"{name} must be finite and non-negative.")
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        t = self._t(); sf = hypot(*t.vector((1, 0)))
        self.elements.append(DistributedLoad(t.point(start), t.point(end), t.vector(direction), label, count,
            None if offset is None else offset*sf, color, lp, lo,
            None if start_height is None else start_height*sf, None if end_height is None else end_height*sf,
            style, cc, z))
        return self

    def udl(self, start: Point, end: Point, *, direction: Vector, height: float, label: str | None = None,
            count: int | None = None, color: str | None = None, label_position: LabelPosition = "auto",
            label_offset: Vector | None = None, style: ElementStyle | None = None, css_class: str | None = None,
            z_index: int = 0) -> Diagram:
        height = finite_scalar("height", height)
        if height <= 0: raise ValueError("height must be positive.")
        return self.distributed_load(start, end, direction=direction, label=label, count=count, offset=height, color=color,
                                     label_position=label_position, label_offset=label_offset, style=style, css_class=css_class, z_index=z_index)

    def varying_load(self, start: Point, end: Point, *, direction: Vector, start_height: float, end_height: float,
                     label: str | None = None, count: int | None = None, color: str | None = None,
                     style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        return self.distributed_load(start, end, direction=direction, label=label, count=count, color=color,
            start_height=start_height, end_height=end_height, style=style, css_class=css_class, z_index=z_index)

    def triangular_load(self, start: Point, end: Point, *, direction: Vector, height: float, peak: Literal["start", "end"] = "end",
                        label: str | None = None, count: int | None = None, color: str | None = None,
                        style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        height = finite_scalar("height", height)
        if height <= 0: raise ValueError("height must be positive.")
        if peak not in {"start", "end"}: raise ValueError("peak must be 'start' or 'end'.")
        return self.varying_load(start, end, direction=direction,
            start_height=height if peak == "start" else 0.0, end_height=height if peak == "end" else 0.0,
            label=label, count=count, color=color, style=style, css_class=css_class, z_index=z_index)

    def moment(self, point: Point, *, clockwise: bool = False, label: str | None = None, radius: float | None = None,
               color: str | None = None, label_position: LabelPosition = "auto", label_offset: Vector | None = None,
               style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        point = finite_point("point", point)
        if radius is not None:
            radius = finite_scalar("radius", radius)
            if radius <= 0: raise ValueError("radius must be positive.")
            radius *= hypot(*self._t().vector((1, 0)))
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        self.elements.append(Moment(self._t().point(point), clockwise, label, radius, color, lp, lo, style, cc, z))
        return self

    def reaction(self, point: Point, vector: Vector, *, label: str | None = None, color: str | None = None,
                 label_position: LabelPosition = "auto", label_offset: Vector | None = None, style: ElementStyle | None = None,
                 css_class: str | None = None, z_index: int = 0) -> Diagram:
        point = finite_point("point", point); vector = finite_vector("vector", vector, nonzero=True)
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        self.elements.append(Reaction(self._t().point(point), self._t().vector(vector), label, color, lp, lo, style, cc, z))
        return self

    def dimension(self, start: Point, end: Point, label: str, *, offset: float = 0.0,
                  label_position: LabelPosition = "auto", label_offset: Vector | None = None,
                  extension_lines: bool = True, endpoint_style: EndpointStyle = "tick", extension_gap: float = 0.08,
                  extension_overrun: float = 0.12, style: ElementStyle | None = None, css_class: str | None = None,
                  z_index: int = 0) -> Diagram:
        start = finite_point("start", start); end = finite_point("end", end)
        if start == end: raise ValueError("A dimension needs two distinct points.")
        offset = finite_scalar("offset", offset); extension_gap = finite_scalar("extension_gap", extension_gap); extension_overrun = finite_scalar("extension_overrun", extension_overrun)
        if extension_gap < 0 or extension_overrun < 0: raise ValueError("extension gap/overrun cannot be negative.")
        if endpoint_style not in _ENDPOINT_STYLES: raise ValueError(f"endpoint_style must be one of {sorted(_ENDPOINT_STYLES)}.")
        lp, lo, cc, z = self._common(label_position, label_offset, css_class, z_index)
        t = self._t(); sf = hypot(*t.vector((1,0)))
        self.elements.append(Dimension(t.point(start), t.point(end), label, offset*sf, lp, lo, extension_lines, endpoint_style,
                                       extension_gap*sf, extension_overrun*sf, style, cc, z))
        return self

    def angle_dimension(self, center: Point, start_angle: float, end_angle: float, radius: float, label: str, *, clockwise: bool = False,
                        style: ElementStyle | None = None, css_class: str | None = None, z_index: int = 0) -> Diagram:
        center=finite_point("center", center); start_angle=finite_scalar("start_angle", start_angle); end_angle=finite_scalar("end_angle", end_angle); radius=finite_scalar("radius", radius)
        if radius <= 0: raise ValueError("radius must be positive.")
        if start_angle == end_angle: raise ValueError("angle dimension needs a non-zero angular span.")
        t=self._t(); sf=hypot(*t.vector((1,0))); rot=atan2(t.c,t.a)*180/pi
        self.elements.append(AngleDimension(t.point(center), start_angle+rot, end_angle+rot, radius*sf, label, clockwise, style, _css_class(css_class), _z(z_index)))
        return self

    def text(self, point: Point, value: str, *, align: Literal["left", "center", "right"] = "center",
             valign: Literal["top", "center", "bottom"] = "bottom", style: ElementStyle | None = None,
             css_class: str | None = None, z_index: int = 0) -> Diagram:
        if align not in {"left", "center", "right"}: raise ValueError("align must be left/center/right.")
        if valign not in {"top", "center", "bottom"}: raise ValueError("valign must be top/center/bottom.")
        self.elements.append(Text(self._t().point(finite_point("point", point)), value, align, valign, style, _css_class(css_class), _z(z_index)))
        return self

    def spring(self, start: Point, end: Point, *, label: str | None = None, style: ElementStyle | None = None,
               css_class: str | None = None, z_index: int = 0) -> Diagram:
        start=finite_point("start",start); end=finite_point("end",end)
        if start==end: raise ValueError("A spring needs two distinct points.")
        self.elements.append(Spring(self._t().point(start), self._t().point(end), label, style, _css_class(css_class), _z(z_index)))
        return self

    def link(self, start: Point, end: Point, *, label: str | None = None, style: ElementStyle | None = None,
             css_class: str | None = None, z_index: int = 0) -> Diagram:
        start=finite_point("start",start); end=finite_point("end",end)
        if start==end: raise ValueError("A link needs two distinct points.")
        self.elements.append(Link(self._t().point(start), self._t().point(end), label, style, _css_class(css_class), _z(z_index)))
        return self

    def axes(self, origin: Point=(0,0), *, x_length: float=1.5, y_length: float=1.5, x_label: str="x", y_label: str="y",
             style: ElementStyle | None=None, css_class: str | None=None, z_index: int=40) -> Diagram:
        origin=finite_point("origin",origin); x_length=finite_scalar("x_length",x_length); y_length=finite_scalar("y_length",y_length)
        if x_length<=0 or y_length<=0: raise ValueError("axis lengths must be positive.")
        t=self._t(); o=t.point(origin)
        self.elements.append(CoordinateAxes(o, t.vector((x_length,0.0)), t.vector((0.0,y_length)), x_label, y_label, style, _css_class(css_class), _z(z_index)))
        return self

    def section_marker(self, point: Point, *, direction: Vector=(0,1), label: str | None=None,
                       style: ElementStyle | None=None, css_class: str | None=None, z_index: int=40) -> Diagram:
        point=finite_point("point",point); direction=finite_vector("direction",direction,nonzero=True)
        self.elements.append(SectionMarker(self._t().point(point), self._t().vector(direction), label, style, _css_class(css_class), _z(z_index)))
        return self

    def leader(self, target: Point, text_point: Point, text: str, *, style: ElementStyle | None=None,
               css_class: str | None=None, z_index: int=45) -> Diagram:
        self.elements.append(Leader(self._t().point(finite_point("target",target)), self._t().point(finite_point("text_point",text_point)), text,
                                    style, _css_class(css_class), _z(z_index)))
        return self

    def displacement(self, point: Point, vector: Vector, *, label: str | None=None, style: ElementStyle | None=None,
                     css_class: str | None=None, z_index: int=35) -> Diagram:
        point=finite_point("point",point); vector=finite_vector("vector",vector,nonzero=True)
        self.elements.append(Displacement(self._t().point(point), self._t().vector(vector), label, style, _css_class(css_class), _z(z_index)))
        return self

    @contextmanager
    def group(self, *, translate: Vector=(0,0), rotate: float=0.0, scale: float=1.0) -> Iterator[Diagram]:
        local = Transform.from_components(translate=translate, rotate_degrees=rotate, scale=scale)
        self._transform_stack.append(local.then(self._t()))
        try:
            yield self
        finally:
            self._transform_stack.pop()

    def add_group(self, other: Diagram, *, translate: Vector=(0,0), rotate: float=0.0, scale: float=1.0, z_offset: int=0) -> Diagram:
        transform = Transform.from_components(translate=translate, rotate_degrees=rotate, scale=scale).then(self._t())
        for element in other.elements:
            self.elements.append(_transform_element(element, transform, z_offset))
        return self

    def extent(self) -> tuple[float, float, float, float]:
        points: list[Point] = []
        for e in self.elements:
            if isinstance(e, (Beam, Spring, Link, Dimension, DistributedLoad)):
                points.extend((e.start, e.end))
            elif isinstance(e, CoordinateAxes):
                points.append(e.origin)
            elif isinstance(e, (Support, Hinge, Moment, Text, SectionMarker, Displacement)):
                points.append(e.point)
            elif isinstance(e, (PointLoad, Reaction)):
                points.extend((e.point, add(e.point, e.vector)))
            elif isinstance(e, Leader): points.extend((e.target, e.text_point))
            elif isinstance(e, (ArcMember, AngleDimension)):
                points.extend(((e.center[0]-e.radius,e.center[1]-e.radius),(e.center[0]+e.radius,e.center[1]+e.radius)))
        if not points: return (-1.0,1.0,-1.0,1.0)
        xs,ys=zip(*points); return min(xs),max(xs),min(ys),max(ys)

    def scale(self, output_width: float | None = None) -> float:
        if self.symbol_scale is not None: return self.symbol_scale
        x0,x1,y0,y1=self.extent(); span=max(x1-x0,y1-y0,1.0)
        if output_width is not None:
            output_width=finite_scalar("output_width",output_width)
            if output_width<=0: raise ValueError("output_width must be positive.")
            return (span/output_width)*0.20
        return span*0.035


def _transform_element(e: DiagramElement, t: Transform, z_offset: int) -> DiagramElement:
    z = e.z_index + z_offset
    if isinstance(e, Beam): return replace(e, start=t.point(e.start), end=t.point(e.end), z_index=z)
    if isinstance(e, ArcMember):
        sf=hypot(*t.vector((1,0))); rot=atan2(t.c,t.a)*180/pi
        return replace(e, center=t.point(e.center), radius=e.radius*sf, start_angle=e.start_angle+rot, end_angle=e.end_angle+rot, z_index=z)
    if isinstance(e, Support):
        tangent=(cos(e.angle*pi/180),sin(e.angle*pi/180)); tv=t.vector(tangent); angle=atan2(tv[1],tv[0])*180/pi
        return replace(e, point=t.point(e.point), angle=angle, z_index=z)
    if isinstance(e, Hinge): return replace(e, point=t.point(e.point), radius=None if e.radius is None else e.radius*hypot(*t.vector((1,0))), z_index=z)
    if isinstance(e, PointLoad): return replace(e, point=t.point(e.point), vector=t.vector(e.vector), z_index=z)
    if isinstance(e, DistributedLoad):
        sf=hypot(*t.vector((1,0)))
        return replace(e,start=t.point(e.start),end=t.point(e.end),direction=t.vector(e.direction),offset=None if e.offset is None else e.offset*sf,
                       start_height=None if e.start_height is None else e.start_height*sf,end_height=None if e.end_height is None else e.end_height*sf,z_index=z)
    if isinstance(e, Moment): return replace(e, point=t.point(e.point), radius=None if e.radius is None else e.radius*hypot(*t.vector((1,0))), z_index=z)
    if isinstance(e, Reaction): return replace(e, point=t.point(e.point), vector=t.vector(e.vector), z_index=z)
    if isinstance(e, Dimension):
        sf=hypot(*t.vector((1,0)))
        return replace(e,start=t.point(e.start),end=t.point(e.end),offset=e.offset*sf,label_offset=None if e.label_offset is None else t.vector(e.label_offset),z_index=z)
    if isinstance(e, AngleDimension):
        sf=hypot(*t.vector((1,0))); rot=atan2(t.c,t.a)*180/pi
        return replace(e,center=t.point(e.center),radius=e.radius*sf,start_angle=e.start_angle+rot,end_angle=e.end_angle+rot,z_index=z)
    if isinstance(e, Text): return replace(e, point=t.point(e.point), z_index=z)
    if isinstance(e, Spring): return replace(e,start=t.point(e.start),end=t.point(e.end),z_index=z)
    if isinstance(e, Link): return replace(e,start=t.point(e.start),end=t.point(e.end),z_index=z)
    if isinstance(e, CoordinateAxes): return replace(e,origin=t.point(e.origin),x_vector=t.vector(e.x_vector),y_vector=t.vector(e.y_vector),z_index=z)
    if isinstance(e, SectionMarker): return replace(e,point=t.point(e.point),direction=t.vector(e.direction),z_index=z)
    if isinstance(e, Leader): return replace(e,target=t.point(e.target),text_point=t.point(e.text_point),z_index=z)
    if isinstance(e, Displacement): return replace(e,point=t.point(e.point),vector=t.vector(e.vector),z_index=z)
    raise TypeError(type(e))
