"""Tests for handling `typing.Any`."""
from typing import Any, Dict, Optional

from attrs import define


@define
class A:
    pass


def test_unstructuring_dict_of_any(converter):
    """Dicts with Any values should use runtime dispatch for their values."""
    assert converter.unstructure({"a": A()}, Dict[str, Any]) == {"a": {}}


def test_unstructuring_any(converter):
    """`Any` should use runtime dispatch."""

    assert converter.unstructure(A(), Any) == {}


def test_unstructure_optional_any(converter):
    """Unstructuring `Optional[Any]` should use the runtime value."""

    assert converter.unstructure(A(), Optional[Any]) == {}
