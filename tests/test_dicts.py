from typing import Any, Dict


def test_any_keys(converter):
    """Dicts with any keys work."""
    assert converter.structure({b"": "1"}, Dict[Any, int]) == {b"": 1}


def test_any_values(converter):
    """Dicts with any values work."""
    assert converter.structure({"1": b"1"}, Dict[int, Any]) == {1: b"1"}
