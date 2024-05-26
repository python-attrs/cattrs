"""Tests for tuples of all kinds."""

from typing import NamedTuple, Tuple

from cattrs.cols import is_namedtuple
from cattrs.converters import Converter


def test_simple_hetero_tuples(genconverter: Converter):
    """Simple heterogenous tuples work.

    Only supported for the Converter (not the BaseConverter).
    """

    genconverter.register_unstructure_hook(int, lambda v: v + 1)

    assert genconverter.unstructure((1, "2"), unstructure_as=Tuple[int, str]) == (
        2,
        "2",
    )

    genconverter.register_structure_hook(int, lambda v, _: v - 1)

    assert genconverter.structure([2, "2"], Tuple[int, str]) == (1, "2")


def test_named_tuple_predicate():
    """The NamedTuple predicate works."""

    assert not is_namedtuple(tuple)
    assert not is_namedtuple(Tuple[int, ...])
    assert not is_namedtuple(Tuple[int])

    class Test(NamedTuple):
        a: int

    assert is_namedtuple(Test)

    class Test2(Tuple[int, int]):
        pass

    assert not is_namedtuple(Test2)


def test_simple_typed_namedtuples(genconverter: Converter):
    """Simple typed namedtuples work."""

    class Test(NamedTuple):
        a: int

    assert genconverter.unstructure(Test(1)) == Test(1)
    assert genconverter.structure([1], Test) == Test(1)

    genconverter.register_unstructure_hook(int, lambda v: v + 1)
    genconverter.register_structure_hook(int, lambda v, _: v - 1)

    assert genconverter.unstructure(Test(1)) == (2,)
    assert genconverter.structure([2], Test) == Test(1)
