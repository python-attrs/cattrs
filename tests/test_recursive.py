"""Test un/structuring recursive class graphs."""
from __future__ import annotations

from typing import List

from attr import define

from cattr import GenConverter


@define
class A:
    inner: List[A]


def test_simple_recursive():
    c = GenConverter()

    orig = A([A([])])
    unstructured = c.unstructure(orig)

    assert unstructured == {"inner": [{"inner": []}]}

    assert c.structure(unstructured, A) == orig
