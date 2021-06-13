from typing import Generic, List, TypeVar, Union

import pytest
from attr import asdict, attrs

from cattr import Converter, GenConverter
from cattr.errors import StructureHandlerNotFoundError

T = TypeVar("T")
T2 = TypeVar("T2")


@attrs(auto_attribs=True)
class TClass(Generic[T, T2]):
    a: T
    b: T2


@pytest.mark.parametrize(
    ("t", "t2", "result"),
    (
        (int, str, TClass(1, "a")),
        (str, str, TClass("1", "a")),
        (List[int], str, TClass([1, 2, 3], "a")),
    ),
)
def test_able_to_structure_generics(converter: Converter, t, t2, result):
    res = converter.structure(asdict(result), TClass[t, t2])

    assert res == result


@pytest.mark.parametrize(
    ("t", "t2", "result"),
    (
        (TClass[int, int], str, TClass(TClass(1, 2), "a")),
        (List[TClass[int, int]], str, TClass([TClass(1, 2)], "a")),
    ),
)
def test_able_to_structure_nested_generics(converter, t, t2, result):
    res = converter.structure(asdict(result), TClass[t, t2])

    assert res == result


def test_able_to_structure_deeply_nested_generics_gen(converter):
    cl = TClass[TClass[TClass[int, int], int], int]
    result = TClass(TClass(TClass(1, 2), 3), 4)

    res = converter.structure(asdict(result), cl)

    assert res == result


def test_structure_unions_of_generics(converter):
    @attrs(auto_attribs=True)
    class TClass2(Generic[T]):
        c: T

    data = TClass2(c="string")
    res = converter.structure(
        asdict(data), Union[TClass[int, int], TClass2[str]]
    )
    assert res == data


def test_structure_list_of_generic_unions(converter):
    @attrs(auto_attribs=True)
    class TClass2(Generic[T]):
        c: T

    data = [TClass2(c="string"), TClass(1, 2)]
    res = converter.structure(
        [asdict(x) for x in data], List[Union[TClass[int, int], TClass2[str]]]
    )
    assert res == data


def test_raises_if_no_generic_params_supplied(converter):
    data = TClass(1, "a")

    with pytest.raises(
        StructureHandlerNotFoundError,
        match="Unsupported type: ~T. Register a structure hook for it.",
    ) as exc:
        converter.structure(asdict(data), TClass)

    assert exc.value.type_ is T

def test_unstructure_generic_attrs():
    c = GenConverter()

    @attrs(auto_attribs=True)
    class Inner(Generic[T]):
        a: T

    @attrs(auto_attribs=True)
    class Outer:
        inner: Inner[int]

    initial = Outer(Inner(1))
    raw = c.unstructure(initial)

    assert raw == {"inner": {"a": 1}}

    new = c.structure(raw, Outer)
    assert initial == new

    @attrs(auto_attribs=True)
    class OuterStr:
        inner: Inner[str]

    assert c.structure(raw, OuterStr) == OuterStr(Inner("1"))
