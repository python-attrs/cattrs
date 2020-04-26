from __future__ import annotations
import attr

from .region import Region


@attr.s(auto_attribs=True, slots=True)
class Roi:
    region1: Region
    region2: Region
