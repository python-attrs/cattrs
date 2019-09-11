"""Loading of attrs classes."""
import attr
import pytest
from hypothesis import given
from hypothesis.strategies import sampled_from
from typing import Optional, List

from cattr.converters import Converter, UnstructureStrategy

unstructure_strats = sampled_from(list(UnstructureStrategy))


@attr.s
class C(object):
    a = attr.ib(type=Optional["C"], default=None)
    b = attr.ib(type=List["C"], factory=list)


@pytest.fixture()
def class_with_forward_ref_attr():
    return C(a=C(), b=[C(), C()])


@given(unstructure_strats)
def test_structure_forward_ref(class_with_forward_ref_attr, strat):
    """
    Classes with forward_ref field can be unstructured and structured.
    """
    converter = Converter(unstruct_strat=strat)

    unstructured_expected = converter.unstructure(class_with_forward_ref_attr)
    structured = converter.structure(unstructured_expected, C)
    unstructured_actual = converter.unstructure(structured)

    assert structured == class_with_forward_ref_attr
    assert unstructured_actual == unstructured_expected
