from typing import Sequence

from attr import has
from hypothesis import given

from cattrs import Converter

from . import nested_classes


def assert_no_attr_classes(obj):
    if isinstance(obj, Sequence):
        for o in obj:
            assert_no_attr_classes(o)
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            assert_no_attr_classes(k)
            assert_no_attr_classes(v)
    else:
        assert not has(obj)


@given(cl=nested_classes)
def test_dumping_to_python(cl, converter: Converter):
    """Dump our generated classes to Python primitives."""
    res = converter.as_python(cl())
    assert isinstance(res, dict)
    assert_no_attr_classes(res)
