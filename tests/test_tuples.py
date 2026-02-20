"""Tests for tuples of all kinds."""

from typing import List, NamedTuple, Tuple

from attrs import Factory, define
from pytest import raises

from cattrs.cols import (
    is_namedtuple,
    namedtuple_dict_structure_factory,
    namedtuple_dict_unstructure_factory,
)
from cattrs.converters import Converter
from cattrs.errors import ForbiddenExtraKeysError


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


def test_simple_dict_nametuples(genconverter: Converter):
    """Namedtuples can be un/structured to/from dicts."""

    class TestInner(NamedTuple):
        a: int

    class Test(NamedTuple):
        a: int
        b: str = "test"
        c: TestInner = TestInner(1)

    genconverter.register_unstructure_hook_factory(
        lambda t: t in (Test, TestInner), namedtuple_dict_unstructure_factory
    )
    genconverter.register_structure_hook_factory(
        lambda t: t in (Test, TestInner), namedtuple_dict_structure_factory
    )

    assert genconverter.unstructure(Test(1)) == {"a": 1, "b": "test", "c": {"a": 1}}
    assert genconverter.structure({"a": 1, "b": "2"}, Test) == Test(
        1, "2", TestInner(1)
    )

    # Defaults work.
    assert genconverter.structure({"a": 1}, Test) == Test(1, "test")


@define
class RecursiveAttrs:
    b: "List[RecursiveNamedtuple]" = Factory(list)


class RecursiveNamedtuple(NamedTuple):
    a: RecursiveAttrs


def test_recursive_dict_nametuples(genconverter: Converter):
    """Recursive namedtuples can be un/structured to/from dicts."""

    genconverter.register_unstructure_hook_factory(
        lambda t: t is RecursiveNamedtuple, namedtuple_dict_unstructure_factory
    )
    genconverter.register_structure_hook_factory(
        lambda t: t is RecursiveNamedtuple, namedtuple_dict_structure_factory
    )

    assert genconverter.unstructure(RecursiveNamedtuple(RecursiveAttrs())) == {
        "a": {"b": []}
    }
    assert genconverter.structure(
        {"a": {}}, RecursiveNamedtuple
    ) == RecursiveNamedtuple(RecursiveAttrs())


def test_dict_nametuples_forbid_extra_keys(genconverter: Converter):
    """Forbidding extra keys works for structuring namedtuples from dicts."""

    class Test(NamedTuple):
        a: int

    genconverter.register_structure_hook_factory(
        lambda t: t is Test,
        lambda t, c: namedtuple_dict_structure_factory(t, c, "from_converter", True),
    )

    with raises(Exception) as exc_info:
        genconverter.structure({"a": 1, "b": "2"}, Test)

    if genconverter.detailed_validation:
        exc = exc_info.value.exceptions[0]
    else:
        exc = exc_info.value

    assert isinstance(exc, ForbiddenExtraKeysError)
    assert exc.extra_fields == {"b"}


def test_dict_namedtuples_detailed_validation():
    """Passing detailed_validation to namedtuple_dict_structure_factory works.

    Regression test for the parameter being passed under the wrong name.
    """

    class Test(NamedTuple):
        a: int

    # Create a converter that does NOT use detailed validation by default.
    c = Converter(detailed_validation=False)

    # But explicitly enable it in the factory.
    c.register_structure_hook_factory(
        lambda t: t is Test,
        lambda t, conv: namedtuple_dict_structure_factory(
            t, conv, detailed_validation=True
        ),
    )

    # With detailed validation, structuring errors should be wrapped
    # in a ClassValidationError instead of being raised directly.
    from cattrs.errors import ClassValidationError

    with raises(ClassValidationError):
        c.structure({"a": "not_an_int"}, Test)
