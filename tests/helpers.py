"""Helpers for tests."""

from typing import Any


def assert_only_unstructured(obj: Any):
    """Assert the object is comprised of only unstructured data:

    * dicts, lists, tuples
    * strings, ints, floats, bools, None
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_only_unstructured(k)
            assert_only_unstructured(v)
    elif isinstance(obj, (list, tuple, frozenset, set)):
        for e in obj:
            assert_only_unstructured(e)
    else:
        assert isinstance(obj, (int, float, str, bool, type(None)))
