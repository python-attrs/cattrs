"""Test un/structuring recursive class graphs."""

from __future__ import annotations

from typing import List

from attr import define

from cattr import Converter


@define
class A:
    inner: List[A]


def test_simple_recursive():
    c = Converter()

    orig = A([A([])])
    unstructured = c.unstructure(orig)

    assert unstructured == {"inner": [{"inner": []}]}

    assert c.structure(unstructured, A) == orig
