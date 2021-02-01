"""Benchmark attrs containing other attrs classes."""
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
