"""Test both structuring and unstructuring."""

from typing import Optional, Union

import pytest
from attrs import define, fields, make_class
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import just, one_of

from cattrs import BaseConverter, UnstructureStrategy

from ._compat import is_py310_plus
from .typed import nested_typed_classes, simple_typed_attrs, simple_typed_classes

unstructure_strats = one_of(just(s) for s in UnstructureStrategy)


@given(simple_typed_classes(newtypes=False, allow_nan=False), unstructure_strats)
def test_simple_roundtrip(cls_and_vals, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    converter = BaseConverter(unstruct_strat=strat)
    cl, vals, kwargs = cls_and_vals
    assume(strat is UnstructureStrategy.AS_DICT or not kwargs)
    inst = cl(*vals, **kwargs)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(
    simple_typed_attrs(defaults=True, newtypes=False, allow_nan=False),
    unstructure_strats,
)
def test_simple_roundtrip_defaults(attr_and_strat, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    a, _ = attr_and_strat
    assume(strat is UnstructureStrategy.AS_DICT or not a.kw_only)
    cl = make_class("HypClass", {"a": a})
    converter = BaseConverter(unstruct_strat=strat)
    inst = cl()
    assert converter.unstructure(converter.structure({}, cl)) == converter.unstructure(
        inst
    )
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(nested_typed_classes(newtypes=False, allow_nan=False))
def test_nested_roundtrip(cls_and_vals):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter = BaseConverter()
    cl, vals, kwargs = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals, **kwargs)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(nested_typed_classes(kw_only=False, newtypes=False, allow_nan=False))
def test_nested_roundtrip_tuple(cls_and_vals):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter = BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
    cl, vals, kwargs = cls_and_vals
    assert not kwargs
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(
    simple_typed_classes(defaults=False, newtypes=False, allow_nan=False),
    simple_typed_classes(defaults=False, newtypes=False, allow_nan=False),
    unstructure_strats,
)
def test_union_field_roundtrip(cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter = BaseConverter(unstruct_strat=strat)
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    assume(strat is UnstructureStrategy.AS_DICT or not kwargs_a)
    cl_b, vals_b, _ = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    assume(len(a_field_names) > len(common_names))

    @define
    class C:
        a: Union[cl_a, cl_b]

    inst = C(a=cl_a(*vals_a, **kwargs_a))

    if strat is UnstructureStrategy.AS_DICT:
        assert inst == converter.structure(converter.unstructure(inst), C)
    else:
        # Our disambiguation functions only support dictionaries for now.
        with pytest.raises(ValueError):
            converter.structure(converter.unstructure(inst), C)

        def handler(obj, _):
            return converter.structure(obj, cl_a)

        converter.register_structure_hook(Union[cl_a, cl_b], handler)
        assert inst == converter.structure(converter.unstructure(inst), C)


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(
    simple_typed_classes(defaults=False, newtypes=False, allow_nan=False),
    simple_typed_classes(defaults=False, newtypes=False, allow_nan=False),
    unstructure_strats,
)
def test_310_union_field_roundtrip(cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter = BaseConverter(unstruct_strat=strat)
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, _ = cl_and_vals_b
    assume(strat is UnstructureStrategy.AS_DICT or not kwargs_a)
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    assume(len(a_field_names) > len(common_names))

    @define
    class C:
        a: cl_a | cl_b

    inst = C(a=cl_a(*vals_a, **kwargs_a))

    if strat is UnstructureStrategy.AS_DICT:
        assert inst == converter.structure(converter.unstructure(inst), C)
    else:
        # Our disambiguation functions only support dictionaries for now.
        with pytest.raises(ValueError):
            converter.structure(converter.unstructure(inst), C)

        def handler(obj, _):
            return converter.structure(obj, cl_a)

        converter.register_structure_hook(cl_a | cl_b, handler)
        assert inst == converter.structure(converter.unstructure(inst), C)


@given(simple_typed_classes(defaults=False, newtypes=False, allow_nan=False))
def test_optional_field_roundtrip(cl_and_vals):
    """
    Classes with optional fields can be unstructured and structured.
    """
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals

    @define
    class C:
        a: Optional[cl]

    inst = C(a=cl(*vals, **kwargs))
    assert inst == converter.structure(converter.unstructure(inst), C)

    inst = C(a=None)
    unstructured = converter.unstructure(inst)

    assert inst == converter.structure(unstructured, C)


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
@given(simple_typed_classes(defaults=False, newtypes=False, allow_nan=False))
def test_310_optional_field_roundtrip(cl_and_vals):
    """
    Classes with optional fields can be unstructured and structured.
    """
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals

    @define
    class C:
        a: cl | None

    inst = C(a=cl(*vals, **kwargs))
    assert inst == converter.structure(converter.unstructure(inst), C)

    inst = C(a=None)
    unstructured = converter.unstructure(inst)

    assert inst == converter.structure(unstructured, C)
