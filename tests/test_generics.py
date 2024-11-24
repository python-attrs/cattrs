from collections import deque
from typing import Deque, Dict, Generic, List, Optional, TypeVar, Union

import pytest
from attrs import asdict, define

from cattrs import BaseConverter, Converter
from cattrs._compat import Protocol
from cattrs._generics import deep_copy_with
from cattrs.errors import StructureHandlerNotFoundError
from cattrs.gen._generics import generate_mapping

from ._compat import Dict_origin, List_origin, is_py310_plus, is_py311_plus

T = TypeVar("T")
T2 = TypeVar("T2")
T3 = TypeVar("T3", bound=int)


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
class TClass(Generic[T, T2, T3]):
    a: T
    b: T2
    c: T3 = 0


@define
class GenericCols(Generic[T]):
    a: T
    b: List[T]
    c: Dict[str, T]


@pytest.mark.parametrize(
    ("t", "t2", "t3", "result"),
    (
        (int, str, int, TClass(1, "a")),
        (str, str, int, TClass("1", "a")),
        (List[int], str, int, TClass([1, 2, 3], "a")),
    ),
)
def test_able_to_structure_generics(converter: BaseConverter, t, t2, t3, result):
    res = converter.structure(asdict(result), TClass[t, t2, t3])

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


@pytest.mark.parametrize(
    ("t", "result"), ((int, (1, [2], {"3": 3})), (str, ("1", ["2"], {"3": "3"})))
)
def test_39_structure_generics_with_cols(t, result, genconverter: Converter):
    @define
    class GenericCols(Generic[T]):
        a: T
        b: list[T]
        c: dict[str, T]

    expected = GenericCols(*result)

    res = genconverter.structure(asdict(expected), GenericCols[t])

    assert res == expected


@pytest.mark.parametrize(("t", "result"), ((int, (1, [1, 2, 3])), (int, (1, None))))
def test_structure_nested_generics_with_cols(t, result, genconverter: Converter):
    @define
    class GenericCols(Generic[T]):
        a: T
        b: Optional[List[T]]

    expected = GenericCols(*result)

    res = genconverter.structure(asdict(expected), GenericCols[t])

    assert res == expected


@pytest.mark.parametrize(
    ("t", "t2", "t3", "result"),
    (
        (TClass[int, int, int], str, int, TClass(TClass(1, 2), "a")),
        (List[TClass[int, int, int]], str, int, TClass([TClass(1, 2)], "a")),
    ),
)
def test_structure_nested_generics(converter: BaseConverter, t, t2, t3, result):
    res = converter.structure(asdict(result), TClass[t, t2, t3])

    assert res == result


def test_able_to_structure_deeply_nested_generics_gen(converter):
    cl = TClass[TClass[TClass[int, int, int], int, int], int, int]
    result = TClass(TClass(TClass(1, 2), 3), 4)

    res = converter.structure(asdict(result), cl)

    assert res == result


def test_structure_unions_of_generics(converter):
    @define
    class TClass2(Generic[T]):
        c: T

    data = TClass2(c="string")
    res = converter.structure(asdict(data), Union[TClass[int, int, int], TClass2[str]])
    assert res == data


def test_structure_list_of_generic_unions(converter):
    @define
    class TClass2(Generic[T]):
        c: T

    data = [TClass2(c="string"), TClass(1, 2)]
    res = converter.structure(
        [asdict(x) for x in data], List[Union[TClass[int, int, int], TClass2[str]]]
    )
    assert res == data


def test_structure_deque_of_generic_unions(converter):
    @define
    class TClass2(Generic[T]):
        c: T

    data = deque((TClass2(c="string"), TClass(1, 2)))
    res = converter.structure(
        [asdict(x) for x in data], Deque[Union[TClass[int, int, int], TClass2[str]]]
    )
    assert res == data


def test_raises_if_no_generic_params_supplied(
    converter: Union[Converter, BaseConverter]
):
    data = TClass(1, "a")

    with pytest.raises(
        StructureHandlerNotFoundError,
        match="Unsupported type: ~T. Register a structure hook for it.|Missing type for generic argument T, specify it when structuring.",
    ) as exc:
        converter.structure(asdict(data), TClass)

    assert exc.value.type_ is T


def test_unstructure_generic_attrs(genconverter):
    @define
    class Inner(Generic[T]):
        a: T

    inner = Inner(Inner(1))
    assert genconverter.unstructure(inner) == {"a": {"a": 1}}

    @define
    class Outer:
        inner: Inner[int]

    initial = Outer(Inner(1))
    raw = genconverter.unstructure(initial)

    assert raw == {"inner": {"a": 1}}

    new = genconverter.structure(raw, Outer)
    assert initial == new

    @define
    class OuterStr:
        inner: Inner[str]

    assert genconverter.structure(raw, OuterStr) == OuterStr(Inner("1"))


def test_unstructure_generic_inheritance(genconverter):
    """Classes inheriting from generic classes work."""
    genconverter.register_unstructure_hook(int, lambda v: v + 1)
    genconverter.register_unstructure_hook(str, lambda v: str(int(v) + 1))

    @define
    class Parent(Generic[T]):
        a: T

    @define
    class Child(Parent, Generic[T]):
        b: str

    instance = Child(1, "2")
    assert genconverter.unstructure(instance, Child[int]) == {"a": 2, "b": "3"}

    @define
    class ExplicitChild(Parent[int]):
        b: str

    instance = ExplicitChild(1, "2")
    assert genconverter.unstructure(instance, ExplicitChild) == {"a": 2, "b": "3"}


def test_unstructure_optional(genconverter):
    """Generics with optional fields work."""

    @define
    class C(Generic[T]):
        a: Union[T, None]

    assert genconverter.unstructure(C(C(1))) == {"a": {"a": 1}}


def test_unstructure_deeply_nested_generics(genconverter):
    @define
    class Inner:
        a: int

    @define
    class Outer(Generic[T]):
        inner: T

    initial = Outer[Inner](Inner(1))
    raw = genconverter.unstructure(initial, Outer[Inner])
    assert raw == {"inner": {"a": 1}}

    raw = genconverter.unstructure(initial)
    assert raw == {"inner": {"a": 1}}


def test_unstructure_deeply_nested_generics_list(genconverter):
    @define
    class Inner:
        a: int

    @define
    class Outer(Generic[T]):
        inner: List[T]

    initial = Outer[Inner]([Inner(1)])
    raw = genconverter.unstructure(initial, Outer[Inner])
    assert raw == {"inner": [{"a": 1}]}

    raw = genconverter.unstructure(initial)
    assert raw == {"inner": [{"a": 1}]}


def test_unstructure_protocol(genconverter):
    class Proto(Protocol):
        a: int

    @define
    class Inner:
        a: int

    @define
    class Outer:
        inner: Proto

    initial = Outer(Inner(1))
    raw = genconverter.unstructure(initial, Outer)
    assert raw == {"inner": {"a": 1}}

    raw = genconverter.unstructure(initial)
    assert raw == {"inner": {"a": 1}}


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
def test_roundtrip_generic_with_union() -> None:
    """Generators should handle classes with unions in their names."""
    c = Converter()

    @define
    class A:
        a: int

    @define
    class B:
        b: int

    @define
    class Outer(Generic[T]):
        member: T

    raw = c.unstructure(Outer(A(1)), unstructure_as=Outer[A | B])
    assert c.structure(raw, Outer[A | B]) == Outer(A(1))


@pytest.mark.skipif(not is_py311_plus, reason="3.11+ only")
def test_generate_typeddict_mapping() -> None:
    from typing import Generic, TypedDict, TypeVar

    T = TypeVar("T")
    U = TypeVar("U")

    class A(TypedDict):
        pass

    assert generate_mapping(A, {}) == {}

    class A(TypedDict, Generic[T]):
        a: T

    assert generate_mapping(A[int], {}) == {T.__name__: int}

    class B(A[int]):
        pass

    assert generate_mapping(B, {}) == {T.__name__: int}

    class C(Generic[T, U]):
        a: T
        c: U

    assert generate_mapping(C[int, U], {}) == {T.__name__: int}


def test_nongeneric_protocols(converter):
    """Non-generic protocols work."""

    class NongenericProtocol(Protocol): ...

    @define
    class Entity(NongenericProtocol): ...

    assert generate_mapping(Entity) == {}

    class GenericProtocol(Protocol[T]): ...

    @define
    class GenericEntity(GenericProtocol[int]):
        a: int

    assert generate_mapping(GenericEntity) == {"T": int}

    assert converter.structure({"a": 1}, GenericEntity) == GenericEntity(1)
