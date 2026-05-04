"""Tests for collections in `cattrs.gen`."""

from typing import Generic, Mapping, NewType, Tuple, TypeVar

from pytest import raises

from cattrs import Converter
from cattrs.errors import IterableValidationError
from cattrs.gen import (
    make_hetero_tuple_structure_fn,
    make_hetero_tuple_unstructure_fn,
    make_mapping_structure_fn,
)


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


def test_structure_hetero_tuple(genconverter: Converter):
    """`make_hetero_tuple_structure_fn` structures heterogeneous tuples."""
    fn = make_hetero_tuple_structure_fn(tuple[int, str], genconverter)

    assert fn(["1", 2], tuple[int, str]) == (1, "2")


def test_structure_hetero_tuple_validation():
    """`make_hetero_tuple_structure_fn` preserves detailed validation."""
    conv = Converter()
    fn = make_hetero_tuple_structure_fn(Tuple[int, int], conv)

    with raises(IterableValidationError) as exc:
        fn(["1", "a"], Tuple[int, int])

    assert exc.value.exceptions[0].__notes__ == [
        "Structuring typing.Tuple[int, int] @ index 1"
    ]
