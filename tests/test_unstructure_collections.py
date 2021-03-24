from typing import Set

import attr
from cattr import GenConverter
from cattr.converters import is_mutable_set, is_sequence, is_mapping
from functools import partial
from cattr._compat import is_py39_plus

if is_py39_plus:
    from collections.abc import MutableSet, Set, Sequence, MutableSequence
else:
    from typing import Set, MutableSet, Sequence, MutableSequence


def test_collection_unstructure_override_set():
    """Test overriding unstructuring sets."""

    # First approach, predicate hook with is_mutable_set
    c = GenConverter()

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
    c = GenConverter(unstruct_collection_overrides={set: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == {
        1,
        2,
        3,
    }
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using abc.MutableSet
    c = GenConverter(unstruct_collection_overrides={MutableSet: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == {1, 2, 3}
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [
        1,
        2,
        3,
    ]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]

    # Second approach, using abc.Set
    c = GenConverter(unstruct_collection_overrides={Set: list})

    assert c.unstructure({1, 2, 3}, unstructure_as=Set[int]) == [1, 2, 3]
    assert c.unstructure({1, 2, 3}, unstructure_as=MutableSet[int]) == [
        1,
        2,
        3,
    ]
    assert c.unstructure({1, 2, 3}) == [1, 2, 3]


def test_collection_unstructure_override_seq():
    """Test overriding unstructuring seq."""

    # First approach, predicate hook
    c = GenConverter()

    c._unstructure_func.register_func_list(
        [
            (
                is_sequence,
                partial(c.gen_unstructure_iterable, unstructure_to=tuple),
                True,
            )
        ]
    )

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == (1, 2, 3)

    @attr.define
    class MyList:
        args = attr.ib(converter=list)

    # Second approach, using abc.MutableSequence
    c = GenConverter(unstruct_collection_overrides={MutableSequence: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure(
        [1, 2, 3], unstructure_as=MutableSequence[int]
    ) == MyList(
        [
            1,
            2,
            3,
        ]
    )
    assert c.unstructure([1, 2, 3]) == MyList(
        [
            1,
            2,
            3,
        ]
    )
    assert c.unstructure((1, 2, 3)) == [
        1,
        2,
        3,
    ]

    # Second approach, using abc.Sequence
    c = GenConverter(unstruct_collection_overrides={Sequence: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == MyList(
        [1, 2, 3]
    )
    assert c.unstructure(
        [1, 2, 3], unstructure_as=MutableSequence[int]
    ) == MyList([1, 2, 3])

    assert c.unstructure([1, 2, 3]) == MyList([1, 2, 3])

    assert c.unstructure((1, 2, 3), unstructure_as=tuple[int, ...]) == MyList(
        [
            1,
            2,
            3,
        ]
    )

    # Second approach, using __builtins__.list
    c = GenConverter(unstruct_collection_overrides={list: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == [
        1,
        2,
        3,
    ]
    assert c.unstructure([1, 2, 3]) == MyList(
        [
            1,
            2,
            3,
        ]
    )
    assert c.unstructure((1, 2, 3)) == [
        1,
        2,
        3,
    ]

    # Second approach, using __builtins__.tuple
    c = GenConverter(unstruct_collection_overrides={tuple: MyList})

    assert c.unstructure([1, 2, 3], unstructure_as=Sequence[int]) == [1, 2, 3]
    assert c.unstructure([1, 2, 3], unstructure_as=MutableSequence[int]) == [
        1,
        2,
        3,
    ]
    assert c.unstructure([1, 2, 3]) == [
        1,
        2,
        3,
    ]
    assert c.unstructure((1, 2, 3)) == MyList(
        [
            1,
            2,
            3,
        ]
    )
