"""Small geometry helpers shared by both rendering backends."""

from __future__ import annotations

from math import cos, pi, sin

from .model import Point, Vector, add, mul, normal, unit


def rotate(vector: Vector, degrees: float) -> Vector:
    angle = degrees * pi / 180.0
    x, y = vector
    return x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle)


def support_axes(angle: float) -> tuple[Vector, Vector]:
    """Return local tangent and outward/downward normal for a support."""
    return rotate((1, 0), angle), rotate((0, -1), angle)


def interpolate(start: Point, end: Point, fraction: float) -> Point:
    return start[0] + (end[0] - start[0]) * fraction, start[1] + (end[1] - start[1]) * fraction


def perpendicular_offset(start: Point, end: Point, amount: float) -> Vector:
    return mul(normal((end[0] - start[0], end[1] - start[1])), amount)


def label_offset(vector: Vector, scale: float, side: float = 1.0) -> Vector:
    return mul(normal(vector), scale * side)


def arrow_head(tip: Point, direction: Vector, scale: float) -> tuple[Point, Point]:
    """Return two rear corners for a symmetric arrowhead ending at ``tip``."""
    ux, uy = unit(direction)
    nx, ny = -uy, ux
    rear = (tip[0] - ux * scale, tip[1] - uy * scale)
    return (
        (rear[0] + nx * scale * 0.48, rear[1] + ny * scale * 0.48),
        (rear[0] - nx * scale * 0.48, rear[1] - ny * scale * 0.48),
    )


def spring_points(
    start: Point, direction: Vector, length: float, width: float, turns: int = 6
) -> list[Point]:
    u = unit(direction)
    n = normal(direction)
    points = [start, add(start, mul(u, length * 0.14))]
    for i in range(turns):
        along = length * (0.14 + (i + 1) * 0.72 / turns)
        sideways = width if i % 2 == 0 else -width
        points.append(add(add(start, mul(u, along)), mul(n, sideways)))
    points.append(add(start, mul(u, length)))
    return points
