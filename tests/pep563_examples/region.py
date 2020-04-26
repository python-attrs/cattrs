from __future__ import annotations
import attr

from .point import Point


class RegionError(RuntimeError):
    pass


@attr.s(auto_attribs=True, slots=True, init=False)
class Region:
    topLeft: Point
    bottomRight: Point

    def __init__(self, topLeft: Point, bottomRight: Point) -> None:
        if not topLeft < bottomRight:
            raise RegionError("topLeft must be less than bottomRight")

        self.topLeft = topLeft
        self.bottomRight = bottomRight
