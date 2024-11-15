from enum import IntEnum
from typing import Dict, List, Mapping, MutableMapping

import attr
import pytest

from cattr import BaseConverter, Converter, UnstructureStrategy


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
        l: List[float]  # noqa: E741
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

    @attr.frozen
    class FrozenCls:
        a: int

    @attr.define
    class C:
        a: Mapping[int, str]
        b: Dict[float, bytes]
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

    @attr.frozen
    class FrozenCls:
        a: int

    @attr.define
    class C:
        a: Mapping[int, str]
        b: Dict[float, bytes]
        c: MutableMapping[int, FrozenCls]

    c = converter_cls()

    inst = C(
        {i: str(i) for i in range(30)},
        {float(i): bytes(i) for i in range(30)},
        {i: FrozenCls(i) for i in range(30)},
    )
    raw = c.unstructure(inst)

    benchmark(c.structure, raw, C)
