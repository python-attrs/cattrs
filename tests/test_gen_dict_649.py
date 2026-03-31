"""`gen` tests under PEP 649 (deferred evaluation of annotations)."""

from dataclasses import dataclass
from typing import TypedDict

from attrs import define

from cattrs import Converter


@define
class A:
    a: A | None  # noqa: F821


@dataclass
class B:
    b: B | None  # noqa: F821


class C(TypedDict):
    c: C | None  # noqa: F821


def test_roundtrip(genconverter: Converter):
    """A simple roundtrip works."""
    initial = A(A(None))
    raw = genconverter.unstructure(initial)

    assert raw == {"a": {"a": None}}
    assert genconverter.structure(raw, A) == initial


def test_roundtrip_dataclass(genconverter: Converter):
    """A simple roundtrip works for dataclasses."""
    initial = B(B(None))
    raw = genconverter.unstructure(initial)

    assert raw == {"b": {"b": None}}
    assert genconverter.structure(raw, B) == initial


def test_roundtrip_typeddict(genconverter: Converter):
    """A simple roundtrip works for TypedDicts."""
    initial: C = {"c": {"c": None}}
    raw = genconverter.unstructure(initial)

    assert raw == {"c": {"c": None}}
    assert genconverter.structure(raw, C) == initial
