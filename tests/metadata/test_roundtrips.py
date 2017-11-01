"""Test both structuring and unstructuring."""
import attr
import pytest

from attr import fields, make_class
from hypothesis import assume, given
from hypothesis.strategies import sampled_from

from cattr import UnstructureStrategy, typed
from typing import Union, Optional

from . import simple_typed_classes, nested_typed_classes, simple_typed_attrs

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


@given(simple_typed_attrs(defaults=True), unstructure_strats)
def test_simple_roundtrip_defaults(converter, cls_and_vals, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    a, _ = cls_and_vals
    cl = make_class("HypClass", {"a": a})
    converter.unstruct_strat = strat
    inst = cl()
    assert converter.unstructure(converter.structure(
        {}, cl)) == converter.unstructure(inst)
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


@given(simple_typed_classes(defaults=False),
       simple_typed_classes(defaults=False),
       unstructure_strats)
def test_union_field_roundtrip(converter, cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter.unstruct_strat = strat
    cl_a, vals_a = cl_and_vals_a
    cl_b, vals_b = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    assume(len(a_field_names) > len(common_names))

    @attr.s
    class C(object):
        a = typed(Union[cl_a, cl_b])

    inst = C(a=cl_a(*vals_a))

    if strat is UnstructureStrategy.AS_DICT:
        assert inst == converter.structure(converter.unstructure(inst), C)
    else:
        # Our disambiguation functions only support dictionaries for now.
        with pytest.raises(ValueError):
            converter.structure(converter.unstructure(inst), C)

        def handler(obj, _):
            return converter.structure(obj, cl_a)

        converter._union_registry[Union[cl_a, cl_b]] = handler
        assert inst == converter.structure(converter.unstructure(inst), C)
        del converter._union_registry[Union[cl_a, cl_b]]


@given(simple_typed_classes(defaults=False))
def test_optional_field_roundtrip(converter, cl_and_vals):
    """
    Classes with optional fields can be unstructured and structured.
    """
    cl, vals = cl_and_vals

    @attr.s
    class C(object):
        a = typed(Optional[cl])

    inst = C(a=cl(*vals))
    assert inst == converter.structure(converter.unstructure(inst), C)

    inst = C(a=None)
    unstructured = converter.unstructure(inst)

    assert inst == converter.structure(unstructured, C)

    del unstructured['a']
    assert inst == converter.structure(unstructured, C)
