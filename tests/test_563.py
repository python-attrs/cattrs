from typing import Tuple, Optional, List, Dict
from cattr.converters import Converter
from hypothesis import given
import hypothesis.strategies as st

from .pep563_examples import point, region, roi, compound

point_strategy = st.tuples(st.integers(min_value=0), st.integers(min_value=0))

# Regions are constructed from two points. The second point must be greater
# than the first
offset_strategy = st.tuples(st.integers(min_value=1), st.integers(min_value=1))
region_strategy = st.tuples(point_strategy, offset_strategy)
roi_strategy = st.tuples(region_strategy, region_strategy)

PointInput = Tuple[int, int]
RegionInput = Tuple[PointInput, PointInput]
RoiInput = Tuple[RegionInput, RegionInput]


def MakePoint(values: PointInput) -> point.Point:
    x, y = values
    return point.Point(x, y)


def MakeRegion(values: RegionInput) -> region.Region:
    point_values, offset_values = values
    x, y = point_values
    offset_x, offset_y = offset_values
    return region.Region(
        MakePoint(point_values), MakePoint((x + offset_x, y + offset_y))
    )


def MakeRoi(values: RoiInput) -> roi.Roi:
    region_1_values, region_2_values = values
    return roi.Roi(MakeRegion(region_1_values), MakeRegion(region_2_values))


def MakeOptionalPoint(values: Optional[PointInput]) -> Optional[point.Point]:
    if values is None:
        return None

    return MakePoint(values)


def MakeOptionalRegion(
    values: Optional[RegionInput],
) -> Optional[region.Region]:

    if values is None:
        return None

    return MakeRegion(values)


def MakeOptionalRoi(values: Optional[RoiInput]) -> Optional[roi.Roi]:
    if values is None:
        return None

    return MakeRoi(values)


@given(point_strategy)
def test_annotated_point(values: PointInput) -> None:
    converter = Converter()
    test_point = MakePoint(values)
    dumped = converter.unstructure(test_point)
    loaded = converter.structure(dumped, point.Point)

    assert test_point == loaded


@given(region_strategy)
def test_annotated_region(values: RegionInput) -> None:
    converter = Converter()
    test_region = MakeRegion(values)
    dumped = converter.unstructure(test_region)
    loaded = converter.structure(dumped, region.Region)

    assert test_region == loaded
    assert type(loaded.topLeft) is point.Point
    assert type(loaded.bottomRight) is point.Point


@given(roi_strategy)
def test_annotated_roi(values: RoiInput) -> None:
    # type: () -> None
    converter = Converter()
    test_roi = MakeRoi(values)
    dumped = converter.unstructure(test_roi)
    loaded = converter.structure(dumped, roi.Roi)

    assert test_roi == loaded
    assert type(loaded.region1) is region.Region
    assert type(loaded.region2) is region.Region

    assert type(loaded.region1.topLeft) is point.Point
    assert type(loaded.region1.bottomRight) is point.Point

    assert type(loaded.region2.topLeft) is point.Point
    assert type(loaded.region2.bottomRight) is point.Point


@given(st.lists(st.integers()))
def test_list_of_ints(list_of_ints: List[int]) -> None:
    converter = Converter()
    p = compound.HasListOfInts(list_of_ints)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasListOfInts)
    assert p == loaded
    assert type(loaded.list_of_ints) is list


@given(st.lists(point_strategy))
def test_list_of_points(values: List[PointInput]) -> None:
    converter = Converter()
    p = compound.HasListOfPoints([MakePoint(i) for i in values])
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasListOfPoints)

    assert p == loaded
    assert type(loaded.list_of_points) is list

    if len(values):
        assert type(loaded.list_of_points[0]) is point.Point


@given(st.lists(region_strategy))
def test_list_of_regions(values: List[RegionInput]) -> None:
    converter = Converter()
    p = compound.HasListOfRegions([MakeRegion(i) for i in values])
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasListOfRegions)

    assert p == loaded
    assert type(loaded.list_of_regions) is list

    if len(values):
        first_region = loaded.list_of_regions[0]
        assert type(first_region) is region.Region
        assert type(first_region.topLeft) is point.Point


@given(st.integers() | st.none())
def test_optional_int(value: Optional[int]) -> None:
    converter = Converter()
    p = compound.HasOptionalInt(value)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalInt)

    assert p == loaded

    if loaded.optional_int is None:
        assert value is None
        return

    assert type(loaded.optional_int) is int


@given(point_strategy | st.none())
def test_optional_point(values: Optional[PointInput]) -> None:
    converter = Converter()
    p = compound.HasOptionalPoint(MakeOptionalPoint(values))
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalPoint)

    assert p == loaded

    if loaded.optional_point is None:
        assert values is None
        return

    assert type(loaded.optional_point) is point.Point
    assert type(loaded.optional_point.x) is int


@given(region_strategy | st.none())
def test_optional_region(values: Optional[RegionInput]) -> None:
    converter = Converter()
    p = compound.HasOptionalRegion(MakeOptionalRegion(values))
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalRegion)

    assert p == loaded

    if loaded.optional_region is None:
        assert values is None
        return

    assert type(loaded.optional_region) is region.Region
    assert type(loaded.optional_region.topLeft) is point.Point


@given(st.lists(st.integers()) | st.none())
def test_optional_list_of_ints(values: Optional[List[int]]) -> None:
    converter = Converter()
    p = compound.HasOptionalListOfInts(values)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalListOfInts)

    assert p == loaded

    if loaded.optional_list_of_ints is None:
        assert values is None
        return

    assert type(loaded.optional_list_of_ints) is list

    if len(loaded.optional_list_of_ints):
        assert type(loaded.optional_list_of_ints[0]) is int


@given(st.lists(point_strategy) | st.none())
def test_optional_list_of_points(values: Optional[List[PointInput]]) -> None:
    converter = Converter()

    inputValue: Optional[List[point.Point]] = None

    if values is not None:
        inputValue = [MakePoint(i) for i in values]

    p = compound.HasOptionalListOfPoints(inputValue)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalListOfPoints)

    assert p == loaded

    if loaded.optional_list_of_points is None:
        assert values is None
        return

    assert type(loaded.optional_list_of_points) is list

    if len(loaded.optional_list_of_points):
        assert type(loaded.optional_list_of_points[0]) is point.Point


@given(st.lists(region_strategy) | st.none())
def test_optional_list_of_regions(values: Optional[List[RegionInput]]) -> None:
    converter = Converter()

    inputValue: Optional[List[region.Region]] = None

    if values is not None:
        inputValue = [MakeRegion(i) for i in values]

    p = compound.HasOptionalListOfRegions(inputValue)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasOptionalListOfRegions)

    assert p == loaded

    if loaded.optional_list_of_regions is None:
        assert values is None
        return

    assert p == loaded

    if loaded.optional_list_of_regions is None:
        assert values is None
        return

    assert type(loaded.optional_list_of_regions) is list

    if len(values):
        first_region = loaded.optional_list_of_regions[0]
        assert type(first_region) is region.Region
        assert type(first_region.topLeft) is point.Point


@given(st.dictionaries(st.text(), st.integers()))
def test_dict_of_ints(values: Dict[str, int]) -> None:
    converter = Converter()
    p = compound.HasDictOfInts(values)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasDictOfInts)

    assert p == loaded
    assert type(loaded.dict_of_ints) is dict

    if len(loaded.dict_of_ints):
        assert type(next(iter(loaded.dict_of_ints.values()))) is int


@given(st.dictionaries(st.text(), point_strategy))
def test_dict_of_points(values: Dict[str, PointInput]) -> None:
    converter = Converter()
    inputValue = {key: MakePoint(value) for key, value in values.items()}
    p = compound.HasDictOfPoints(inputValue)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasDictOfPoints)

    assert p == loaded
    assert type(loaded.dict_of_points) is dict

    if len(loaded.dict_of_points):
        assert type(next(iter(loaded.dict_of_points.values()))) is point.Point


@given(st.dictionaries(st.text(), region_strategy))
def test_dict_of_regions(values: Dict[str, RegionInput]) -> None:
    converter = Converter()
    inputValue = {key: MakeRegion(value) for key, value in values.items()}
    p = compound.HasDictOfRegions(inputValue)
    dumped = converter.unstructure(p)
    loaded = converter.structure(dumped, compound.HasDictOfRegions)

    assert p == loaded
    assert type(loaded.dict_of_regions) is dict

    if len(loaded.dict_of_regions):
        any_region = next(iter(loaded.dict_of_regions.values()))
        assert type(any_region) is region.Region
        assert type(any_region.bottomRight) is point.Point
