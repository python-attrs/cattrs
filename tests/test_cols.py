"""Tests for the `cattrs.cols` module."""

from collections.abc import MutableSequence, Sequence, Set
from typing import Dict

from immutables import Map

from cattrs import BaseConverter, Converter
from cattrs._compat import FrozenSet
from cattrs.cols import (
    is_abstract_set,
    is_any_set,
    is_sequence,
    iterable_unstructure_factory,
    list_structure_factory,
    mapping_unstructure_factory,
)

from ._compat import is_py310_plus


def test_set_overriding(converter: BaseConverter):
    """Overriding abstract sets by wrapping the default factory works."""

    converter.register_unstructure_hook_factory(
        is_any_set,
        lambda t, c: iterable_unstructure_factory(t, c, unstructure_to=sorted),
    )

    assert converter.unstructure({"c", "b", "a"}, Set[str]) == ["a", "b", "c"]
    assert converter.unstructure(frozenset(["c", "b", "a"]), FrozenSet[str]) == [
        "a",
        "b",
        "c",
    ]


def test_structuring_immutables_map(genconverter: Converter):
    """This should work due to our new is_mapping predicate."""
    assert genconverter.structure({"a": 1}, Map[str, int]) == Map(a=1)


def test_mapping_unstructure_direct(genconverter: Converter):
    """Some cases reduce to just `dict`."""
    assert genconverter.get_unstructure_hook(Dict[str, int]) is dict

    # `dict` is equivalent to `dict[Any, Any]`, which should not reduce to
    # just `dict`.
    assert genconverter.get_unstructure_hook(dict) is not dict

    if is_py310_plus:
        assert genconverter.get_unstructure_hook(dict[str, int]) is dict


def test_mapping_unstructure_to(genconverter: Converter):
    """`unstructure_to` works."""
    hook = mapping_unstructure_factory(Dict[str, str], genconverter, unstructure_to=Map)
    assert hook({"a": "a"}).__class__ is Map


def test_structure_sequences(converter: BaseConverter):
    """Sequences are structured to tuples."""

    assert converter.structure(["1", 2, 3.0], Sequence[int]) == (1, 2, 3)


def test_structure_sequences_override(converter: BaseConverter):
    """Sequences can be overriden to structure to lists, as previously."""

    converter.register_structure_hook_factory(is_sequence, list_structure_factory)

    assert converter.structure(["1", 2, 3.0], Sequence[int]) == [1, 2, 3]


def test_structure_mut_sequences(converter: BaseConverter):
    """Mutable sequences are structured to lists."""

    assert converter.structure(["1", 2, 3.0], MutableSequence[int]) == [1, 2, 3]


def test_abstract_set_predicate():
    """`is_abstract_set` works."""

    assert is_abstract_set(Set)
    assert is_abstract_set(Set[str])

    assert not is_abstract_set(set)
    assert not is_abstract_set(set[str])


def test_structure_abstract_sets(converter: BaseConverter):
    """Abstract sets structure to frozensets."""

    assert converter.structure(["1", "2", "3"], Set[int]) == frozenset([1, 2, 3])
    assert isinstance(converter.structure([1, 2, 3], Set[int]), frozenset)


def test_structure_abstract_sets_override(converter: BaseConverter):
    """Abstract sets can be overridden to structure to mutable sets, as before."""
    converter.register_structure_hook_func(is_abstract_set, converter._structure_set)

    assert converter.structure(["1", 2, 3.0], Set[int]) == {1, 2, 3}
