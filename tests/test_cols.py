"""Tests for the `cattrs.cols` module."""

from cattrs import BaseConverter
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
