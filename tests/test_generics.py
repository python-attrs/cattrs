from typing import Dict, Generic, List, Optional, TypeVar, Union

import pytest
from attr import asdict, attrs, define

from cattrs import BaseConverter, Converter
from cattrs._compat import Protocol, is_py39_plus
from cattrs._generics import deep_copy_with
from cattrs.errors import StructureHandlerNotFoundError

from ._compat import Dict_origin, List_origin

T = TypeVar("T")
T2 = TypeVar("T2")


def test_deep_copy():
    """Test the deep copying of generic parameters."""
    mapping = {T.__name__: int}
    assert deep_copy_with(Optional[T], mapping) == Optional[int]
    assert (
        deep_copy_with(List_origin[Optional[T]], mapping) == List_origin[Optional[int]]
    )
    mapping = {T.__name__: int, T2.__name__: str}
    assert (
        deep_copy_with(Dict_origin[T2, List_origin[Optional[T]]], mapping)
        == Dict_origin[str, List_origin[Optional[int]]]
    )


@define
class TClass(Generic[T, T2]):
    a: T
    b: T2


@define
class GenericCols(Generic[T]):
    a: T
    b: List[T]
    c: Dict[str, T]


@pytest.mark.parametrize(
    ("t", "t2", "result"),
    (
        (int, str, TClass(1, "a")),
        (str, str, TClass("1", "a")),
        (List[int], str, TClass([1, 2, 3], "a")),
    ),
)
def test_able_to_structure_generics(converter: BaseConverter, t, t2, result):
    res = converter.structure(asdict(result), TClass[t, t2])

    assert res == result


@pytest.mark.parametrize(
    ("t", "result"),
    ((int, GenericCols(1, [2], {"3": 3})), (str, GenericCols("1", ["2"], {"3": "3"}))),
)
@pytest.mark.parametrize("detailed_validation", [True, False])
def test_structure_generics_with_cols(t, result, detailed_validation):
    raw = asdict(result)
    res = Converter(detailed_validation=detailed_validation).structure(
        raw, GenericCols[t]
    )

    assert res == result


@pytest.mark.skipif(not is_py39_plus, reason="3.9+ generics syntax")
@pytest.mark.parametrize(
    ("t", "result"), ((int, (1, [2], {"3": 3})), (str, ("1", ["2"], {"3": "3"})))
)
def test_39_structure_generics_with_cols(t, result):
    @define
    class GenericCols(Generic[T]):
        a: T
        b: list[T]
        c: dict[str, T]

    expected = GenericCols(*result)

    res = Converter().structure(asdict(expected), GenericCols[t])

    assert res == expected


@pytest.mark.parametrize(("t", "result"), ((int, (1, [1, 2, 3])), (int, (1, None))))
def test_structure_nested_generics_with_cols(t, result):
    @define
    class GenericCols(Generic[T]):
        a: T
        b: Optional[List[T]]

    expected = GenericCols(*result)

    res = Converter().structure(asdict(expected), GenericCols[t])

    assert res == expected


@pytest.mark.parametrize(
    ("t", "t2", "result"),
    (
        (TClass[int, int], str, TClass(TClass(1, 2), "a")),
        (List[TClass[int, int]], str, TClass([TClass(1, 2)], "a")),
    ),
)
def test_structure_nested_generics(converter: BaseConverter, t, t2, result):
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
    res = converter.structure(asdict(data), Union[TClass[int, int], TClass2[str]])
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
        match="Unsupported type: ~T. Register a structure hook for it.|Missing type for generic argument T, specify it when structuring.",
    ) as exc:
        converter.structure(asdict(data), TClass)

    assert exc.value.type_ is T


def test_unstructure_generic_attrs():
    c = Converter()

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


def test_unstructure_deeply_nested_generics():
    c = Converter()

    @define
    class Inner:
        a: int

    @define
    class Outer(Generic[T]):
        inner: T

    initial = Outer[Inner](Inner(1))
    raw = c.unstructure(initial, Outer[Inner])
    assert raw == {"inner": {"a": 1}}

    raw = c.unstructure(initial)
    assert raw == {"inner": {"a": 1}}


def test_unstructure_deeply_nested_generics_list():
    c = Converter()

    @define
    class Inner:
        a: int

    @define
    class Outer(Generic[T]):
        inner: List[T]

    initial = Outer[Inner]([Inner(1)])
    raw = c.unstructure(initial, Outer[Inner])
    assert raw == {"inner": [{"a": 1}]}

    raw = c.unstructure(initial)
    assert raw == {"inner": [{"a": 1}]}


def test_unstructure_protocol():
    c = Converter()

    class Proto(Protocol):
        a: int

    @define
    class Inner:
        a: int

    @define
    class Outer:
        inner: Proto

    initial = Outer(Inner(1))
    raw = c.unstructure(initial, Outer)
    assert raw == {"inner": {"a": 1}}

    raw = c.unstructure(initial)
    assert raw == {"inner": {"a": 1}}
