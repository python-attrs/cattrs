"""Benchmark attrs containing other attrs classes."""

import pytest
from attrs import define

from cattr import BaseConverter, Converter, UnstructureStrategy


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_attrs_nested(benchmark, converter_cls, unstructure_strat):
    c = converter_cls(unstruct_strat=unstructure_strat)

    @define
    class InnerA:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class InnerB:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class InnerC:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class InnerD:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class InnerE:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class Outer:
        a: InnerA
        b: InnerB
        c: InnerC
        d: InnerD
        e: InnerE

    inst = Outer(
        InnerA(1, 1.0, "one", b"one"),
        InnerB(2, 2.0, "two", b"two"),
        InnerC(3, 3.0, "three", b"three"),
        InnerD(4, 4.0, "four", b"four"),
        InnerE(5, 5.0, "five", b"five"),
    )

    benchmark(c.unstructure, inst)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstruct_attrs_deep_nest(benchmark, converter_cls, unstructure_strat):
    c = converter_cls(unstruct_strat=unstructure_strat)

    @define
    class InnerA:
        a: int
        b: float
        c: str
        d: bytes

    @define
    class InnerB:
        a: InnerA
        b: InnerA
        c: InnerA
        d: InnerA

    @define
    class InnerC:
        a: InnerB
        b: InnerB
        c: InnerB
        d: InnerB

    @define
    class InnerD:
        a: InnerC
        b: InnerC
        c: InnerC
        d: InnerC

    @define
    class InnerE:
        a: InnerD
        b: InnerD
        c: InnerD
        d: InnerD

    @define
    class Outer:
        a: InnerE
        b: InnerE
        c: InnerE
        d: InnerE

    def make_inner_a():
        return InnerA(1, 1.0, "one", b"one")

    def make_inner_b():
        return InnerB(*[make_inner_a() for _ in range(4)])

    def make_inner_c():
        return InnerC(*[make_inner_b() for _ in range(4)])

    def make_inner_d():
        return InnerD(*[make_inner_c() for _ in range(4)])

    def make_inner_e():
        return InnerE(*[make_inner_d() for _ in range(4)])

    inst = Outer(*[make_inner_e() for _ in range(4)])

    benchmark(c.unstructure, inst)
