"""Tests for PEP 695 (Type Parameter Syntax)."""
from dataclasses import dataclass

import pytest
from attrs import define

from cattrs import BaseConverter, Converter

from ._compat import is_py312_plus


@pytest.mark.skipif(not is_py312_plus, reason="3.12+ syntax")
def test_simple_generic_roundtrip(converter: BaseConverter):
    """PEP 695 attrs generics work."""

    @define
    class A[T]:
        a: T

    assert converter.structure({"a": "1"}, A[int]) == A(1)
    assert converter.unstructure(A(1)) == {"a": 1}

    if isinstance(converter, Converter):
        # Only supported on a Converter
        assert converter.unstructure(A(1), A[int]) == {"a": 1}


@pytest.mark.skipif(not is_py312_plus, reason="3.12+ syntax")
def test_simple_generic_roundtrip_dc(converter: BaseConverter):
    """PEP 695 dataclass generics work."""

    @dataclass
    class A[T]:
        a: T

    assert converter.structure({"a": "1"}, A[int]) == A(1)
    assert converter.unstructure(A(1)) == {"a": 1}

    if isinstance(converter, Converter):
        # Only supported on a Converter
        assert converter.unstructure(A(1), A[int]) == {"a": 1}
