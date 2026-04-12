
from collections import deque
from collections.abc import Callable, Collection, Iterable, MutableSequence, MutableSet, Sequence, Set
from typing import Any, Union

import pytest

from attrs import define
from cattrs.converters import BaseConverter
from cattrs.strategies import configure_union_single_collection_dispatch


@define
class CollectionParameter:
    type_factory: Callable[[Any], type[Collection]]
    factory: Callable[[Iterable], Collection]


@pytest.fixture(
    params=[
        pytest.param(CollectionParameter(lambda t: deque[t], deque), id="deque"),
        pytest.param(CollectionParameter(lambda t: frozenset[t], frozenset), id="frozenset"),
        pytest.param(CollectionParameter(lambda t: list[t], list), id="list"),
        pytest.param(CollectionParameter(lambda t: MutableSequence[t], list), id="MutableSequence"),
        pytest.param(CollectionParameter(lambda t: MutableSet[t], set), id="MutableSet"),
        pytest.param(CollectionParameter(lambda t: Sequence[t], tuple), id="Sequence"),
        pytest.param(CollectionParameter(lambda t: Set[t], frozenset), id="Set"),
        pytest.param(CollectionParameter(lambda t: set[t], set), id="set"),
        pytest.param(CollectionParameter(lambda t: tuple[t, ...], tuple), id="tuple"),
    ],
)
def collection(request: pytest.FixtureRequest) -> CollectionParameter:
    return request.param


def test_works_with_simple_union(converter: BaseConverter, collection: CollectionParameter):
    configure_union_single_collection_dispatch(converter)

    union = Union[collection.type_factory(str) | str]

    assert converter.structure("abcd", union) == "abcd"
    assert converter.structure("abcd", str) == "abcd"


    expected_structured = collection.factory(["abcd"])
    assert converter.structure(["abcd"], union) == expected_structured
    assert converter.structure(["abcd"], collection.type_factory(str)) == expected_structured
    assert converter.structure(deque(["abcd"]), union) == expected_structured
    assert converter.structure(deque(["abcd"]), collection.type_factory(str)) == expected_structured
    assert converter.structure(frozenset(["abcd"]), union) == expected_structured
    assert converter.structure(frozenset(["abcd"]), collection.type_factory(str)) == expected_structured
    assert converter.structure(set(["abcd"]), union) == expected_structured
    assert converter.structure(set(["abcd"]), collection.type_factory(str)) == expected_structured
    assert converter.structure(tuple(["abcd"]), union) == expected_structured
    assert converter.structure(tuple(["abcd"]), collection.type_factory(str)) == expected_structured


def test_apply_union_disambiguation(converter: BaseConverter, collection: CollectionParameter):
    configure_union_single_collection_dispatch(converter)

    @define(frozen=True)
    class A:
        a: int

    @define(frozen=True)
    class B:
        b: int
    
    collection_type = collection.type_factory(Union[A, B])
    union = Union[collection_type, A, B]

    assert converter.structure({"a": 1}, union) == A(1)
    assert converter.structure({"a": 1}, Union[A, B]) == A(1)
    assert converter.structure({"a": 1}, A) == A(1)
    assert converter.structure({"b": 2}, union) == B(2)
    assert converter.structure({"b": 2}, Union[A, B]) == B(2)
    assert converter.structure({"b": 2}, B) == B(2)

    expected_structured = collection.factory([A(1), B(2)])
    assert converter.structure([{"a": 1}, {"b": 2}], union) == expected_structured
    assert converter.structure([{"a": 1}, {"b": 2}], collection_type) == expected_structured
    assert converter.structure(deque([{"a": 1}, {"b": 2}]), union) == expected_structured
    assert converter.structure(deque([{"a": 1}, {"b": 2}]), collection_type) == expected_structured
    assert converter.structure(tuple([{"a": 1}, {"b": 2}]), union) == expected_structured
    assert converter.structure(tuple([{"a": 1}, {"b": 2}]), collection_type) == expected_structured
