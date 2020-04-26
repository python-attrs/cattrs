from __future__ import annotations
from typing import List, Dict, Optional

import attr

from .point import Point
from .region import Region

# It is not clear to me how create hypothesis tests that create random input
# files, so I have manually created a few test cases here.
#
# These classes are used to test whether compound types can resolve properly:
#   'List[int]' -> typing.List[int]
#   'Dict[str, Point]' -> typing.Dict[str, point.Point]
#   'Optional[List[int]' -> typing.Union[typing.List[int], NoneType]


@attr.s(auto_attribs=True)
class HasListOfInts:
    list_of_ints: List[int] = attr.ib(factory=list)


@attr.s(auto_attribs=True)
class HasListOfPoints:
    list_of_points: List[Point] = attr.ib(factory=list)


@attr.s(auto_attribs=True)
class HasListOfRegions:
    list_of_regions: List[Region] = attr.ib(factory=list)


@attr.s(auto_attribs=True)
class HasOptionalInt:
    optional_int: Optional[int]


@attr.s(auto_attribs=True)
class HasOptionalPoint:
    optional_point: Optional[Point]


@attr.s(auto_attribs=True)
class HasOptionalRegion:
    optional_region: Optional[Region]


@attr.s(auto_attribs=True)
class HasOptionalListOfInts:
    optional_list_of_ints: Optional[List[int]]


@attr.s(auto_attribs=True)
class HasOptionalListOfPoints:
    optional_list_of_points: Optional[List[Point]]


@attr.s(auto_attribs=True)
class HasOptionalListOfRegions:
    optional_list_of_regions: Optional[List[Region]]


@attr.s(auto_attribs=True)
class HasDictOfInts:
    dict_of_ints: Dict[str, int] = attr.ib(factory=dict)


@attr.s(auto_attribs=True)
class HasDictOfPoints:
    dict_of_points: Dict[str, Point] = attr.ib(factory=dict)


@attr.s(auto_attribs=True)
class HasDictOfRegions:
    dict_of_regions: Dict[str, Region] = attr.ib(factory=dict)
