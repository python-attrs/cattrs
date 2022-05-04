from collections import Counter
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from functools import partial

import attr
import pytest
from immutables import Map

from cattrs import Converter
from cattrs._compat import is_py39_plus
from cattrs.converters import is_mutable_set, is_sequence


@pytest.mark.skipif(not is_py39_plus, reason="Requires Python 3.9+")
def test_collection_unstructure_override_set():
    """Test overriding unstructuring sets."""

    # First approach, predicate hook with is_mutable_set
    c = Converter()

    c._unstructure_func.register_func_list(
        [
            (
                is_mutable_set,
                partial(c.gen_unstructure_iterable, unstructure_to=list),
                True,
            )
        ]
    )

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]

    # Second approach, using __builtins__.set
    c = Converter(unstruct_collection_overrides={set: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using abc.MutableSet
    c = Converter(unstruct_collection_overrides={MutableSet: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using abc.Set
    c = Converter(unstruct_collection_overrides={Set: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]


@pytest.mark.skipif(is_py39_plus, reason="Requires Python 3.8 or lower")
def test_collection_unstructure_override_set_38():
    """Test overriding unstructuring sets."""
    from typing import AbstractSet, MutableSet, Set

    # First approach, predicate hook with is_mutable_set
    c = Converter()

    c._unstructure_func.register_func_list(
        [
            (
                is_mutable_set,
                partial(c.gen_unstructure_iterable, unstructure_to=list),
                True,
            )
        ]
    )

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]

    # Second approach, using __builtins__.set
    c = Converter(unstruct_collection_overrides={set: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using typing.MutableSet
    c = Converter(unstruct_collection_overrides={MutableSet: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using typing.AbstractSet
    c = Converter(unstruct_collection_overrides={AbstractSet: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]


@pytest.mark.skipif(not is_py39_plus, reason="Requires Python 3.9+")
def test_collection_unstructure_override_seq():
    """Test overriding unstructuring seq."""

    # First approach, predicate hook
    c = Converter()

    c._unstructure_func.register_func_list(
        [(is_sequence, partial(c.gen_unstructure_iterable, unstructure_to=tuple), True)]
    )

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == (1, 2, 3)

    @attr.define
    class MyList:
        args = attr.ib(converter=list)

    # Second approach, using abc.MutableSequence
    c = Converter(unstruct_collection_overrides={MutableSequence: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == MyList(
        [1, 2, 3]
    )
    assert c.unstructure([1, 2, 3]) == MyList([1, 2, 3])
    assert c.unstructure((1, 2, 3)) == [1, 2, 3]

    # Second approach, using abc.Sequence
    c = Converter(unstruct_collection_overrides={Sequence: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == MyList([1, 2, 3])
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == MyList(
        [1, 2, 3]
    )

    assert c.unstructure([1, 2, 3]) == MyList([1, 2, 3])

    assert c.unstructure((1, 2, 3), unstructure_as=tuple[int, ...]) == MyList([1, 2, 3])

    # Second approach, using __builtins__.list
    c = Converter(unstruct_collection_overrides={list: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3]) == MyList([1, 2, 3])
    assert c.unstructure((1, 2, 3)) == [1, 2, 3]

    # Second approach, using __builtins__.tuple
    c = Converter(unstruct_collection_overrides={tuple: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3]) == [1, 2, 3]
    assert c.unstructure((1, 2, 3)) == MyList([1, 2, 3])


@pytest.mark.skipif(not is_py39_plus, reason="Requires Python 3.9+")
def test_collection_unstructure_override_mapping():
    """Test overriding unstructuring mappings."""

    # Using Counter
    c = Converter(unstruct_collection_overrides={Counter: Map})
    assert c.unstructure(Counter({1: 2})) == Map({1: 2})
    assert c.unstructure(Counter({1: 2}), unstructure_as=Counter[int]) == Map({1: 2})
    assert c.unstructure({1: 2}) == {1: 2}
    assert c.unstructure({1: 2}, unstructure_as=MutableMapping[int, int]) == {1: 2}
    assert c.unstructure({1: 2}, unstructure_as=Mapping[int, int]) == {1: 2}

    # Using __builtins__.dict
    c = Converter(unstruct_collection_overrides={dict: Map})

    assert c.unstructure(Counter({1: 2})) == Map({1: 2})
    assert c.unstructure(Counter({1: 2}), unstructure_as=Counter[int]) == Map({1: 2})
    assert c.unstructure({1: 2}) == Map({1: 2})
    assert c.unstructure({1: 2}, unstructure_as=MutableMapping[int, int]) == {1: 2}
    assert c.unstructure({1: 2}, unstructure_as=Mapping[int, int]) == {1: 2}

    # Using MutableMapping
    c = Converter(unstruct_collection_overrides={MutableMapping: Map})

    assert c.unstructure(Counter({1: 2})) == Map({1: 2})
    assert c.unstructure(Counter({1: 2}), unstructure_as=Counter[int]) == Map({1: 2})
    assert c.unstructure({1: 2}) == Map({1: 2})
    assert c.unstructure({1: 2}, unstructure_as=MutableMapping[int, int]) == Map({1: 2})
    assert c.unstructure({1: 2}, unstructure_as=Mapping[int, int]) == {1: 2}

    # Using Mapping
    c = Converter(unstruct_collection_overrides={Mapping: Map})

    assert c.unstructure(Counter({1: 2})) == Map({1: 2})
    assert c.unstructure(Counter({1: 2}), unstructure_as=Counter[int]) == Map({1: 2})
    assert c.unstructure({1: 2}) == Map({1: 2})
    assert c.unstructure({1: 2}, unstructure_as=MutableMapping[int, int]) == Map({1: 2})
    assert c.unstructure({1: 2}, unstructure_as=Mapping[int, int]) == Map({1: 2})
