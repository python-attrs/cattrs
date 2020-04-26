from __future__ import annotations
import attr


@attr.s(auto_attribs=True, slots=True)
class Point:
    x: int
    y: int
