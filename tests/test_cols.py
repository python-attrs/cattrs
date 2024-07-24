"""Tests for the `cattrs.cols` module."""

from immutables import Map

from cattrs import BaseConverter, Converter
from cattrs._compat import AbstractSet, FrozenSet
from cattrs.cols import is_any_set, iterable_unstructure_factory


def test_set_overriding(converter: BaseConverter):
    """Overriding abstract sets by wrapping the default factory works."""

    converter.register_unstructure_hook_factory(
        is_any_set,
        lambda t, c: iterable_unstructure_factory(t, c, unstructure_to=sorted),
    )

    assert converter.unstructure({"c", "b", "a"}, AbstractSet[str]) == ["a", "b", "c"]
    assert converter.unstructure(frozenset(["c", "b", "a"]), FrozenSet[str]) == [
        "a",
        "b",
        "c",
    ]


def test_structuring_immutables_map(genconverter: Converter):
    """This should work due to our new is_mapping predicate."""
    assert genconverter.structure({"a": 1}, Map[str, int]) == Map(a=1)
