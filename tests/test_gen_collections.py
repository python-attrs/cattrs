"""Tests for collections in `cattrs.gen`."""

from typing import Generic, Mapping, NewType, Tuple, TypeVar

from cattrs import Converter
from cattrs.gen import make_hetero_tuple_unstructure_fn, make_mapping_structure_fn


def test_structuring_mappings(genconverter: Converter):
    """The `key_type` parameter works for generics with 1 type variable."""
    T = TypeVar("T")

    class MyMapping(Generic[T], Mapping[str, T]):
        pass

    def key_hook(value, _):
        return f"{value}1"

    Key = NewType("Key", str)

    genconverter.register_structure_hook(Key, key_hook)

    fn = make_mapping_structure_fn(MyMapping[int], genconverter, key_type=Key)

    assert fn({"a": 1}, MyMapping[int]) == {"a1": 1}


def test_unstructure_hetero_tuple_to_tuple(genconverter: Converter):
    """`make_hetero_tuple_unstructure_fn` works when unstructuring to tuple."""
    fn = make_hetero_tuple_unstructure_fn(Tuple[int, str, int], genconverter, tuple)

    assert fn((1, "1", 2)) == (1, "1", 2)
