"""Tests for tuples under PEP 563 (stringified annotations)."""

from __future__ import annotations

from typing import NamedTuple

from cattrs import Converter
from cattrs.cols import (
    namedtuple_dict_structure_factory,
    namedtuple_dict_unstructure_factory,
)


class NT(NamedTuple):
    a: int


def test_simple_dict_nametuples(genconverter: Converter):
    """Namedtuples can be un/structured to/from dicts."""

    class Test(NamedTuple):
        a: int
        b: str = "test"

    genconverter.register_unstructure_hook_factory(
        lambda t: t is Test, namedtuple_dict_unstructure_factory
    )
    genconverter.register_structure_hook_factory(
        lambda t: t is Test, namedtuple_dict_structure_factory
    )

    assert genconverter.unstructure(Test(1)) == {"a": 1, "b": "test"}
    assert genconverter.structure({"a": 1, "b": "2"}, Test) == Test(1, "2")

    # Defaults work.
    assert genconverter.structure({"a": 1}, Test) == Test(1, "test")
