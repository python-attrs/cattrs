from enum import IntEnum
from typing import List

import attr
import pytest

from cattr import Converter, GenConverter, UnstructureStrategy


@pytest.mark.parametrize(
    "converter_cls",
    [Converter, GenConverter],
)
@pytest.mark.parametrize(
    "unstructure_strat",
    [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE],
)
def test_unstructure_attrs_lists_small(
    benchmark, converter_cls, unstructure_strat
):
    """
    Benchmark a small (3 attributes) attrs class containing lists of primitives.
    """

    @attr.define
    class C:
        a: List[int]
        b: List[float]
        c: List[str]

    c = converter_cls(unstruct_strat=unstructure_strat)

    benchmark(
        c.unstructure,
        C(
            [1, 2, 3],
            [1.0, 2.0, 3.0],
            ["a small string", "another string", "third string"],
        ),
    )


@pytest.mark.parametrize(
    "converter_cls",
    [Converter, GenConverter],
)
@pytest.mark.parametrize(
    "unstructure_strat",
    [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE],
)
def test_unstructure_attrs_lists_med(
    benchmark, converter_cls, unstructure_strat
):
    """
    Benchmark a medium (10 attributes) attrs class containing lists of
    primitives.
    """

    class E(IntEnum):
        ONE = 1
        TWO = 2

    @attr.define
    class C:
        a: List[int]
        b: List[float]
        c: List[str]
        d: List[bytes]
        e: List[E]
        f: List[int]
        g: List[float]
        h: List[str]
        i: List[bytes]
        j: List[E]

    c = converter_cls(unstruct_strat=unstructure_strat)

    benchmark(
        c.unstructure,
        C(
            [1] * 5,
            [1.0] * 5,
            ["a small string"] * 5,
            ["test".encode()] * 5,
            [E.ONE] * 5,
            [2] * 5,
            [2.0] * 5,
            ["a small string"] * 5,
            ["test".encode()] * 5,
            [E.TWO] * 5,
        ),
    )


@pytest.mark.parametrize(
    "converter_cls",
    [Converter, GenConverter],
)
@pytest.mark.parametrize(
    "unstructure_strat",
    [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE],
)
def test_unstructure_attrs_lists_large(
    benchmark, converter_cls, unstructure_strat
):
    """
    Benchmark a large (30 attributes) attrs class containing lists of
    primitives.
    """

    class E(IntEnum):
        ONE = 1
        TWO = 2

    @attr.define
    class C:
        a: List[int]
        b: List[float]
        c: List[str]
        d: List[bytes]
        e: List[E]
        f: List[int]
        g: List[float]
        h: List[str]
        i: List[bytes]
        j: List[E]
        k: List[int]
        l: List[float]
        m: List[str]
        n: List[bytes]
        o: List[E]
        p: List[int]
        q: List[float]
        r: List[str]
        s: List[bytes]
        t: List[E]
        u: List[int]
        v: List[float]
        w: List[str]
        x: List[bytes]
        y: List[E]
        z: List[int]
        aa: List[float]
        ab: List[str]
        ac: List[bytes]
        ad: List[E]

    c = converter_cls(unstruct_strat=unstructure_strat)

    benchmark(
        c.unstructure,
        C(
            [1] * 3,
            [1.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.ONE] * 3,
            [2] * 3,
            [2.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.TWO] * 3,
            [3] * 3,
            [3.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.ONE] * 3,
            [4] * 3,
            [4.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.TWO] * 3,
            [5] * 3,
            [5.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.ONE] * 3,
            [6] * 3,
            [6.0] * 3,
            ["a small string"] * 3,
            ["test".encode()] * 3,
            [E.TWO] * 3,
        ),
    )
