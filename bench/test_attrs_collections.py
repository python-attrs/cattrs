from enum import IntEnum
from typing import Mapping, MutableMapping

import pytest
from attrs import define, frozen

from cattrs import BaseConverter, Converter, UnstructureStrategy


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_attrs_lists(benchmark, converter_cls, unstructure_strat):
    """
    Benchmark a large (30 attributes) attrs class containing lists of
    primitives.
    """

    class E(IntEnum):
        ONE = 1
        TWO = 2

    @define
    class C:
        a: list[int]
        b: list[float]
        c: list[str]
        d: list[bytes]
        e: list[E]
        f: list[int]
        g: list[float]
        h: list[str]
        i: list[bytes]
        j: list[E]
        k: list[int]
        l: list[float]  # noqa: E741
        m: list[str]
        n: list[bytes]
        o: list[E]
        p: list[int]
        q: list[float]
        r: list[str]
        s: list[bytes]
        t: list[E]
        u: list[int]
        v: list[float]
        w: list[str]
        x: list[bytes]
        y: list[E]
        z: list[int]
        aa: list[float]
        ab: list[str]
        ac: list[bytes]
        ad: list[E]

    c = converter_cls(unstruct_strat=unstructure_strat)

    benchmark(
        c.unstructure,
        C(
            [1] * 3,
            [1.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.ONE] * 3,
            [2] * 3,
            [2.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.TWO] * 3,
            [3] * 3,
            [3.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.ONE] * 3,
            [4] * 3,
            [4.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.TWO] * 3,
            [5] * 3,
            [5.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.ONE] * 3,
            [6] * 3,
            [6.0] * 3,
            ["a small string"] * 3,
            [b"test"] * 3,
            [E.TWO] * 3,
        ),
    )


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_attrs_mappings(benchmark, converter_cls, unstructure_strat):
    """
    Benchmark an attrs class containing mappings.
    """

    @frozen
    class FrozenCls:
        a: int

    @define
    class C:
        a: Mapping[int, str]
        b: dict[float, bytes]
        c: MutableMapping[int, FrozenCls]

    c = converter_cls(unstruct_strat=unstructure_strat)

    benchmark(
        c.unstructure,
        C(
            {i: str(i) for i in range(30)},
            {float(i): bytes(i) for i in range(30)},
            {i: FrozenCls(i) for i in range(30)},
        ),
    )


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_attrs_mappings(benchmark, converter_cls):
    """
    Benchmark an attrs class containing mappings.
    """

    @frozen
    class FrozenCls:
        a: int

    @define
    class C:
        a: Mapping[int, str]
        b: dict[float, bytes]
        c: MutableMapping[int, FrozenCls]

    c = converter_cls()

    inst = C(
        {i: str(i) for i in range(30)},
        {float(i): bytes(i) for i in range(30)},
        {i: FrozenCls(i) for i in range(30)},
    )
    raw = c.unstructure(inst)

    benchmark(c.structure, raw, C)
