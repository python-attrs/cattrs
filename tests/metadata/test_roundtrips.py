"""Test both structuring and unstructuring."""
from hypothesis import given

from attr import fields

from . import simple_typed_classes, nested_typed_classes


@given(simple_typed_classes())
def test_simple_roundtrip(converter, cls_and_vals):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    cl, vals = cls_and_vals
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(nested_typed_classes)
def test_nested_roundtrip(converter, cls_and_vals):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    cl, vals = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    attr_names = [a.name for a in fields(cl)]
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)
