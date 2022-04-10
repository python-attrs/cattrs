"""Benchmark attrs containing other attrs classes."""
import attr
import pytest

from cattr import BaseConverter, Converter, UnstructureStrategy


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_attrs_nested(benchmark, converter_cls, unstructure_strat):
    c = converter_cls(unstruct_strat=unstructure_strat)

    @attr.define
    class InnerA:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class InnerB:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class InnerC:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class InnerD:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class InnerE:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class Outer:
        a: InnerA
        b: InnerB
        c: InnerC
        d: InnerD
        e: InnerE

    inst = Outer(
        InnerA(1, 1.0, "one", "one".encode()),
        InnerB(2, 2.0, "two", "two".encode()),
        InnerC(3, 3.0, "three", "three".encode()),
        InnerD(4, 4.0, "four", "four".encode()),
        InnerE(5, 5.0, "five", "five".encode()),
    )

    benchmark(c.unstructure, inst)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstruct_attrs_deep_nest(benchmark, converter_cls, unstructure_strat):
    c = converter_cls(unstruct_strat=unstructure_strat)

    @attr.define
    class InnerA:
        a: int
        b: float
        c: str
        d: bytes

    @attr.define
    class InnerB:
        a: InnerA
        b: InnerA
        c: InnerA
        d: InnerA

    @attr.define
    class InnerC:
        a: InnerB
        b: InnerB
        c: InnerB
        d: InnerB

    @attr.define
    class InnerD:
        a: InnerC
        b: InnerC
        c: InnerC
        d: InnerC

    @attr.define
    class InnerE:
        a: InnerD
        b: InnerD
        c: InnerD
        d: InnerD

    @attr.define
    class Outer:
        a: InnerE
        b: InnerE
        c: InnerE
        d: InnerE

    make_inner_a = lambda: InnerA(1, 1.0, "one", "one".encode())
    make_inner_b = lambda: InnerB(*[make_inner_a() for _ in range(4)])
    make_inner_c = lambda: InnerC(*[make_inner_b() for _ in range(4)])
    make_inner_d = lambda: InnerD(*[make_inner_c() for _ in range(4)])
    make_inner_e = lambda: InnerE(*[make_inner_d() for _ in range(4)])

    inst = Outer(*[make_inner_e() for _ in range(4)])

    benchmark(c.unstructure, inst)
