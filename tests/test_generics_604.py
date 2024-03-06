"""Tests for generics under PEP 604 (unions as pipes)."""

from typing import Generic, TypeVar

from attrs import define

T = TypeVar("T")


def test_unstructure_optional(genconverter):
    """Generics with optional fields work."""

    @define
    class C(Generic[T]):
        a: T | None

    assert genconverter.unstructure(C(C(1))) == {"a": {"a": 1}}
