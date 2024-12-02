"""Tests for defaultdicts."""

from collections import defaultdict
from typing import DefaultDict

from cattrs import Converter
from cattrs.cols import defaultdict_structure_factory


def test_typing_defaultdicts(genconverter: Converter):
    """`typing.DefaultDict` works."""
    res = genconverter.structure({"a": 1}, DefaultDict[str, int])

    assert isinstance(res, defaultdict)
    assert res["a"] == 1
    assert res["b"] == 0

    genconverter.register_unstructure_hook(int, str)

    assert genconverter.unstructure(res) == {"a": "1", "b": "0"}


def test_collection_defaultdicts(genconverter: Converter):
    """`collections.defaultdict` works."""
    res = genconverter.structure({"a": 1}, defaultdict[str, int])

    assert isinstance(res, defaultdict)
    assert res["a"] == 1
    assert res["b"] == 0

    genconverter.register_unstructure_hook(int, str)

    assert genconverter.unstructure(res) == {"a": "1", "b": "0"}


def test_factory(genconverter: Converter):
    """Explicit factories work."""
    genconverter.register_structure_hook_func(
        lambda t: t == defaultdict[str, int],
        defaultdict_structure_factory(defaultdict[str, int], genconverter, lambda: 2),
    )
    res = genconverter.structure({"a": 1}, defaultdict[str, int])

    assert isinstance(res, defaultdict)
    assert res["a"] == 1
    assert res["b"] == 2
