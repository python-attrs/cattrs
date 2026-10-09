"""Tests for `structure_attrs_fromtuple`/`structure_attrs_fromdict` under PEP 563 (stringified annotations).

Regression tests for https://github.com/python-attrs/cattrs/issues/293:
with `from __future__ import annotations`, attribute types are strings,
so dispatching on them finds no structure hooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attrs import define

from cattrs import Converter


# These need to be at the top level for `attrs.resolve_types` to work.
@define
class AttrsClass:
    a: int


@dataclass
class Dataclass:
    a: int


def _structure_int(val: str, _: Any) -> int:
    return int(val)


def _int_hook_converter() -> Converter:
    converter = Converter()
    converter.register_structure_hook(int, _structure_int)
    return converter


def test_structure_attrs_fromtuple_pep563():
    """`structure_attrs_fromtuple` resolves stringified annotations."""
    converter = _int_hook_converter()

    assert converter.structure_attrs_fromtuple(["1"], AttrsClass) == AttrsClass(1)


def test_structure_attrs_fromdict_pep563():
    """`structure_attrs_fromdict` resolves stringified annotations."""
    converter = _int_hook_converter()

    assert converter.structure_attrs_fromdict({"a": "1"}, AttrsClass) == AttrsClass(1)


def test_structure_attrs_fromtuple_pep563_dataclass():
    """`structure_attrs_fromtuple` resolves stringified annotations on dataclasses."""
    converter = _int_hook_converter()

    assert converter.structure_attrs_fromtuple(["1"], Dataclass) == Dataclass(1)


def test_structure_attrs_fromdict_pep563_dataclass():
    """`structure_attrs_fromdict` resolves stringified annotations on dataclasses."""
    converter = _int_hook_converter()

    assert converter.structure_attrs_fromdict({"a": "1"}, Dataclass) == Dataclass(1)
