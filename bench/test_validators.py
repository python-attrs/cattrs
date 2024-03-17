"""Benchmarks for validators."""
import pytest
from attrs import define
from attrs import fields as f

from cattrs import Converter
from cattrs.v import V, customize, greater_than, len_between


@define
class Small:
    a: int
    b: str


@pytest.mark.parametrize("dv", [True, False])
def test_structure_success(dv: bool, benchmark):
    c = Converter(detailed_validation=dv)

    hook = customize(
        c,
        Small,
        V((fs := f(Small)).a).ensure(greater_than(10)),
        V(fs.b).ensure(len_between(0, 10)),
    )

    d = {"a": 11, "b": "abcde"}

    benchmark(hook, d, None)
