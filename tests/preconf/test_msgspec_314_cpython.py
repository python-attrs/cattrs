"""Tests for msgspec functionality on Python 3.14."""

from attrs import define
from msgspec import to_builtins

from cattrs.preconf.msgspec import make_converter


@define
class RecursiveAttrs:
    children: list[RecursiveAttrs]  # noqa: F821


def test_unstructure_recursive_attrs_class_with_self_list():
    """Unstructuring recursive data structures under 3.14 works."""
    converter = make_converter()

    inst = RecursiveAttrs([RecursiveAttrs([])])
    raw = {"children": [{"children": []}]}

    assert converter.get_unstructure_hook(RecursiveAttrs) is to_builtins
    assert converter.unstructure(inst) == raw
    assert converter.structure(raw, RecursiveAttrs) == inst
