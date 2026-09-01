"""Geometry helpers shared by both rendering backends."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, isfinite, pi, sin

Point = tuple[float, float]
Vector = tuple[float, float]


def finite_scalar(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def finite_point(name: str, point: Point) -> Point:
    if len(point) != 2:
        raise ValueError(f"{name} must contain exactly two coordinates.")
    return finite_scalar(f"{name}[0]", point[0]), finite_scalar(f"{name}[1]", point[1])


def finite_vector(name: str, vector: Vector, *, nonzero: bool = False) -> Vector:
    vector = finite_point(name, vector)
    if nonzero and hypot(*vector) == 0:
        raise ValueError(f"{name} cannot be zero.")
    return vector


def unit(vector: Vector) -> Vector:
    x, y = finite_vector("direction vector", vector, nonzero=True)
    length = hypot(x, y)
    return x / length, y / length


def normal(vector: Vector) -> Vector:
    x, y = unit(vector)
    return -y, x


def add(a: Point, b: Vector) -> Point:
    return a[0] + b[0], a[1] + b[1]


def sub(a: Point, b: Point) -> Vector:
    return a[0] - b[0], a[1] - b[1]


def mul(vector: Vector, amount: float) -> Vector:
    return vector[0] * amount, vector[1] * amount


def length(vector: Vector) -> float:
    return hypot(*vector)


def rotate(vector: Vector, degrees: float) -> Vector:
    degrees = finite_scalar("angle", degrees)
    angle = degrees * pi / 180.0
    x, y = vector
    return x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle)


def interpolate(start: Point, end: Point, fraction: float) -> Point:
    return start[0] + (end[0] - start[0]) * fraction, start[1] + (end[1] - start[1]) * fraction


def arrow_head(tip: Point, direction: Vector, scale: float) -> tuple[Point, Point]:
    ux, uy = unit(direction)
    nx, ny = -uy, ux
    rear = tip[0] - ux * scale, tip[1] - uy * scale
    return (
        rear[0] + nx * scale * 0.48, rear[1] + ny * scale * 0.48
    ), (
        rear[0] - nx * scale * 0.48, rear[1] - ny * scale * 0.48
    )


def spring_points(start: Point, direction: Vector, length_: float, width: float, turns: int = 6) -> list[Point]:
    u = unit(direction)
    n = normal(direction)
    points = [start, add(start, mul(u, length_ * 0.14))]
    for i in range(turns):
        along = length_ * (0.14 + (i + 1) * 0.72 / turns)
        sideways = width if i % 2 == 0 else -width
        points.append(add(add(start, mul(u, along)), mul(n, sideways)))
    points.append(add(start, mul(u, length_)))
    return points


@dataclass(frozen=True)
class Transform:
    """Simple 2-D affine transform used by diagram groups."""

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    tx: float = 0.0
    ty: float = 0.0

    @classmethod
    def from_components(
        cls, *, translate: Vector = (0.0, 0.0), rotate_degrees: float = 0.0, scale: float = 1.0,
        mirror_x: bool = False,
    ) -> "Transform":
        finite_vector("translate", translate)
        rotate_degrees = finite_scalar("rotate", rotate_degrees)
        scale = finite_scalar("scale", scale)
        if scale <= 0:
            raise ValueError("group scale must be positive.")
        theta = rotate_degrees * pi / 180.0
        sx = -scale if mirror_x else scale
        sy = scale
        return cls(
            a=cos(theta) * sx,
            b=-sin(theta) * sy,
            c=sin(theta) * sx,
            d=cos(theta) * sy,
            tx=translate[0], ty=translate[1],
        )

    def point(self, p: Point) -> Point:
        return self.a * p[0] + self.b * p[1] + self.tx, self.c * p[0] + self.d * p[1] + self.ty

    def vector(self, v: Vector) -> Vector:
        return self.a * v[0] + self.b * v[1], self.c * v[0] + self.d * v[1]

    def then(self, outer: "Transform") -> "Transform":
        """Apply self, then outer."""
        return Transform(
            a=outer.a * self.a + outer.b * self.c,
            b=outer.a * self.b + outer.b * self.d,
            c=outer.c * self.a + outer.d * self.c,
            d=outer.c * self.b + outer.d * self.d,
            tx=outer.a * self.tx + outer.b * self.ty + outer.tx,
            ty=outer.c * self.tx + outer.d * self.ty + outer.ty,
        )

    def rotation_degrees(self) -> float:
        from math import atan2
        return atan2(self.c, self.a) * 180.0 / pi
