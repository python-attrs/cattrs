"""Tests for generics under PEP 696 (type defaults)."""

from typing import Generic, List

import pytest
from attrs import define, fields
from typing_extensions import TypeVar

from cattrs.errors import StructureHandlerNotFoundError
from cattrs.gen import generate_mapping

T = TypeVar("T")
TD = TypeVar("TD", default=str)


def test_structure_typevar_default(genconverter):
    """Generics with defaulted TypeVars work."""

    @define
    class C(Generic[T]):
        a: T

    c_mapping = generate_mapping(C)
    atype = fields(C).a.type
    assert atype.__name__ not in c_mapping

    with pytest.raises(StructureHandlerNotFoundError):
        # Missing type for generic argument
        genconverter.structure({"a": "1"}, C)

    c_mapping = generate_mapping(C[str])
    atype = fields(C[str]).a.type
    assert c_mapping[atype.__name__] is str

    assert genconverter.structure({"a": "1"}, C[str]) == C("1")

    @define
    class D(Generic[TD]):
        a: TD

    d_mapping = generate_mapping(D)
    atype = fields(D).a.type
    assert d_mapping[atype.__name__] is str

    # Defaults to string
    assert d_mapping[atype.__name__] is str
    assert genconverter.structure({"a": "1"}, D) == D("1")

    # But allows other types
    assert genconverter.structure({"a": "1"}, D[str]) == D("1")
    assert genconverter.structure({"a": 1}, D[int]) == D(1)


def test_unstructure_iterable(genconverter):
    """Unstructuring iterables with defaults works."""
    genconverter.register_unstructure_hook(str, lambda v: v + "_str")

    @define
    class C(Generic[TD]):
        a: List[TD]

    assert genconverter.unstructure(C(["a"])) == {"a": ["a_str"]}
    assert genconverter.unstructure(["a"], List[TD]) == ["a_str"]
