"""Test both structuring and unstructuring."""
from hypothesis import given
from hypothesis.strategies import sampled_from

from cattr import UnstructureStrategy

from . import simple_typed_classes, nested_typed_classes

unstructure_strats = sampled_from(list(UnstructureStrategy))


@given(simple_typed_classes(), unstructure_strats)
def test_simple_roundtrip(converter, cls_and_vals, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    converter.unstruct_strat = strat
    cl, vals = cls_and_vals
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(nested_typed_classes, unstructure_strats)
def test_nested_roundtrip(converter, cls_and_vals, strat):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter.unstruct_strat = strat
    cl, vals = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)
