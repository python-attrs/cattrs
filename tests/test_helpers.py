"""Tests for test helpers."""

import pytest
from attrs import define

from .helpers import assert_only_unstructured


def test_assert_only_unstructured_passes_for_primitives():
    """assert_only_unstructured should pass for basic Python data types."""
    # Test primitives
    assert_only_unstructured(42)
    assert_only_unstructured("hello")
    assert_only_unstructured(3.14)
    assert_only_unstructured(True)
    assert_only_unstructured(None)

    # Test collections of primitives
    assert_only_unstructured([1, 2, 3])
    assert_only_unstructured({"key": "value", "number": 42})
    assert_only_unstructured((1, "two", 3.0))
    assert_only_unstructured({1, 2, 3})
    assert_only_unstructured(frozenset([1, 2, 3]))

    # Test nested structures
    assert_only_unstructured(
        {"list": [1, 2, {"nested": "dict"}], "tuple": (True, None), "number": 42}
    )


def test_assert_only_unstructured_fails_for_attrs_classes():
    """assert_only_unstructured should fail for attrs classes."""

    @define
    class SimpleAttrsClass:
        value: int

    instance = SimpleAttrsClass(42)

    # Should raise AssertionError for attrs class instance
    with pytest.raises(AssertionError):
        assert_only_unstructured(instance)

    # Should also fail when attrs instance is nested in collections
    with pytest.raises(AssertionError):
        assert_only_unstructured([instance])

    with pytest.raises(AssertionError):
        assert_only_unstructured({"key": instance})

    with pytest.raises(AssertionError):
        assert_only_unstructured((1, instance, 3))
