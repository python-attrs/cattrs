"""Tests for defaultdicts."""
from collections import defaultdict
from typing import DefaultDict

from cattrs import Converter


def test_typing_defaultdicts(genconverter: Converter):
    res = genconverter.structure({"a": 1}, DefaultDict[str, int])

    assert isinstance(res, defaultdict)
    assert res["a"] == 1
    assert res["b"] == 0


def test_collection_defaultdicts(genconverter: Converter):
    res = genconverter.structure({"a": 1}, defaultdict[str, int])

    assert isinstance(res, defaultdict)
    assert res["a"] == 1
    assert res["b"] == 0
