"""Tests for handling `typing.Any`."""
from typing import Any, Dict

from attrs import define


@define
class A:
    pass


def test_unstructuring_dict_of_any(converter):
    """Dicts with Any values should use runtime dispatch for their values."""
    assert converter.unstructure({"a": A()}, Dict[str, Any]) == {"a": {}}
