"""Tests un/structure of nested generic classes (stringified only)"""

from __future__ import annotations

from typing import Generic, TypeVar

from attrs import define

T = TypeVar("T")


def test_structure_nested_roundtrip(genconverter):
    @define(auto_attribs=True)
    class Inner:
        value: int

    @define(auto_attribs=True)
    class Container(Generic[T]):
        data: T

    raw = {"data": {"value": 42}}
    structured = genconverter.structure(raw, Container[Inner])
    assert genconverter.unstructure(structured, Container[Inner]) == raw
