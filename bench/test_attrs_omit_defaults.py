from enum import IntEnum

import attr
import pytest

from cattr import BaseConverter, Converter, UnstructureStrategy


class E(IntEnum):
    ONE = 1
    TWO = 2


@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_omit_primitive_defaults(benchmark, unstructure_strat):
    """Benchmark stripping default values with simple, non-factory primitives."""
    c = Converter(unstruct_strat=unstructure_strat, omit_if_default=True)

    @attr.define
    class C:
        a: int = 0
        b: float = 0.0
        c: str = "test"
        d: bytes = b"test"
        e: E = E.ONE
        f: int = 0
        g: float = 0.0
        h: str = "test"
        i: bytes = b"test"
        j: E = E.ONE
        k: int = 0
        l: float = 0.0 # noqa: E741
        m: str = "test"
        n: bytes = b"test"
        o: E = E.ONE
        p: int = 0
        q: float = 0.0
        r: str = "test"
        s: bytes = b"test"
        t: E = E.ONE
        u: int = 0
        v: float = 0.0
        w: str = "test"
        x: bytes = b"test"
        y: E = E.ONE
        z: int = 0
        aa: float = 0.0
        ab: str = "test"
        ac: bytes = b"test"
        ad: E = E.ONE

    c_instance = C()

    benchmark(
        c.unstructure,
        c_instance,
    )

@pytest.mark.parametrize(
    "unstructure_strat", [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)
def test_unstructure_omit_factory_defaults(benchmark, unstructure_strat):
    """Benchmark stripping default values with factory-made primitives."""
    c = Converter(unstruct_strat=unstructure_strat, omit_if_default=True)

    @attr.define
    class C:
        a: dict = attr.field(factory=dict)
        b: list = attr.field(factory=list)
        c: tuple = attr.field(factory=tuple)
        d: set = attr.field(factory=set)

    c_instance = C()

    benchmark(
        c.unstructure,
        c_instance,
    )
