"""Tests for PEP 649 (Deferred Evaluation Of Annotations Using Descriptors)."""

from __future__ import annotations

from typing import Generic, TypeVar

from attrs import define

from cattrs import Converter

T = TypeVar("T")


@define
class GenericClass(Generic[T]):
    t: T


def test_generics_with_stringified_annotations():
    """Type resolution works with stringified annotations."""
    converter = Converter()
    inst = GenericClass(42)
    dct = converter.unstructure(inst, unstructure_as=GenericClass[int])
    assert dct == {"t": 42}
    assert converter.structure(dct, GenericClass[int])
