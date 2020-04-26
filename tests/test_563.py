from cattr.converters import Converter
from hypothesis import given
import hypothesis.strategies as st

from .pep563_examples import point, region, roi


@given(st.integers(), st.integers())
def test_annotated_point(x, y):
    # type: (int, int) -> None
    converter = Converter()
    test_point = point.Point(x, y)
    dumped = converter.unstructure(test_point)
    loaded = converter.structure(dumped, point.Point)

    assert test_point == loaded


def test_annotated_region():
    # type: () -> None
    converter = Converter()
    test_region = region.Region(point.Point(0, 0), point.Point(100, 200))
    dumped = converter.unstructure(test_region)
    loaded = converter.structure(dumped, region.Region)

    assert test_region == loaded
    assert type(loaded.topLeft) is point.Point
    assert type(loaded.bottomRight) is point.Point


def test_annotated_roi():
    # type: () -> None
    converter = Converter()

    test_roi = roi.Roi(
        region.Region(point.Point(0, 0), point.Point(100, 200)),
        region.Region(point.Point(0, 210), point.Point(100, 390)))

    dumped = converter.unstructure(test_roi)
    loaded = converter.structure(dumped, roi.Roi)

    assert test_roi == loaded
    assert type(loaded.region1) is region.Region
    assert type(loaded.region2) is region.Region

    assert type(loaded.region1.topLeft) is point.Point
    assert type(loaded.region1.bottomRight) is point.Point

    assert type(loaded.region2.topLeft) is point.Point
    assert type(loaded.region2.bottomRight) is point.Point
