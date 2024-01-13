"""Tests for collections in `cattrs.gen`."""
from typing import Generic, Mapping, NewType, TypeVar

from cattrs import Converter
from cattrs.gen import make_mapping_structure_fn


def test_structuring_mappings(converter: Converter):
    """The `key_type` parameter works for generics with 1 type variable."""
    T = TypeVar("T")

    class MyMapping(Generic[T], Mapping[str, T]):
        pass

    def key_hook(value, _):
        return f"{value}1"

    Key = NewType("Key", str)

    converter.register_structure_hook(Key, key_hook)

    fn = make_mapping_structure_fn(MyMapping[int], converter, key_type=Key)

    assert fn({"a": 1}, MyMapping[int]) == {"a1": 1}
