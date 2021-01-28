"""Test both structuring and unstructuring."""
from typing import Optional, Union

import attr
import pytest
from attr import Factory, fields, make_class
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import booleans, sampled_from

from cattr import GenConverter as Converter
from cattr import UnstructureStrategy
from cattr.gen import override

from . import nested_typed_classes, simple_typed_attrs, simple_typed_classes

unstructure_strats = sampled_from(list(UnstructureStrategy))


@given(simple_typed_classes(), unstructure_strats)
def test_simple_roundtrip(cls_and_vals, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    converter = Converter(unstruct_strat=strat)
    cl, vals = cls_and_vals
    inst = cl(*vals)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(simple_typed_attrs(defaults=True), unstructure_strats)
def test_simple_roundtrip_defaults(cls_and_vals, strat):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    a, _ = cls_and_vals
    cl = make_class("HypClass", {"a": a})
    converter = Converter(unstruct_strat=strat)
    inst = cl()
    assert converter.unstructure(
        converter.structure({}, cl)
    ) == converter.unstructure(inst)
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(
    nested_typed_classes(defaults=True, min_attrs=1),
    unstructure_strats,
    booleans(),
)
def test_nested_roundtrip(cls_and_vals, strat, omit_if_default):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter = Converter(
        unstruct_strat=strat, omit_if_default=omit_if_default
    )
    cl, vals = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals)
    unstructured = converter.unstructure(inst)
    assert inst == converter.structure(unstructured, cl)


@settings(
    suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow]
)
@given(
    simple_typed_classes(defaults=False),
    simple_typed_classes(defaults=False),
    unstructure_strats,
)
def test_union_field_roundtrip(cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter = Converter(unstruct_strat=strat)
    cl_a, vals_a = cl_and_vals_a
    cl_b, _ = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    assume(len(a_field_names) > len(common_names))

    @attr.s
    class C(object):
        a = attr.ib(type=Union[cl_a, cl_b])

    inst = C(a=cl_a(*vals_a))

    if strat is UnstructureStrategy.AS_DICT:
        unstructured = converter.unstructure(inst)
        assert inst == converter.structure(
            converter.unstructure(unstructured), C
        )
    else:
        # Our disambiguation functions only support dictionaries for now.
        with pytest.raises(ValueError):
            converter.structure(converter.unstructure(inst), C)

        def handler(obj, _):
            return converter.structure(obj, cl_a)

        converter.register_structure_hook(Union[cl_a, cl_b], handler)
        unstructured = converter.unstructure(inst)
        assert inst == converter.structure(unstructured, C)


@given(simple_typed_classes(defaults=False))
def test_optional_field_roundtrip(cl_and_vals):
    """
    Classes with optional fields can be unstructured and structured.
    """
    converter = Converter()
    cl, vals = cl_and_vals

    @attr.s
    class C(object):
        a = attr.ib(type=Optional[cl])

    inst = C(a=cl(*vals))
    assert inst == converter.structure(converter.unstructure(inst), C)

    inst = C(a=None)
    unstructured = converter.unstructure(inst)

    assert inst == converter.structure(unstructured, C)


@given(simple_typed_classes(defaults=True))
def test_omit_default_roundtrip(cl_and_vals):
    """
    Omit default on the converter works.
    """
    converter = Converter(omit_if_default=True)
    cl, vals = cl_and_vals

    @attr.s
    class C(object):
        a: int = attr.ib(default=1)
        b: cl = attr.ib(factory=lambda: cl(*vals))

    inst = C()
    unstructured = converter.unstructure(inst)
    assert unstructured == {}
    assert inst == converter.structure(unstructured, C)

    inst = C(0)
    unstructured = converter.unstructure(inst)
    assert unstructured == {"a": 0}
    assert inst == converter.structure(unstructured, C)


@given(simple_typed_classes(defaults=True))
def test_type_overrides(cl_and_vals):
    """
    Type overrides on the GenConverter work.
    """
    converter = Converter(type_overrides={int: override(omit_if_default=True)})
    cl, vals = cl_and_vals

    inst = cl(*vals)
    unstructured = converter.unstructure(inst)

    for field, val in zip(fields(cl), vals):
        if field.type is int:
            if field.default is not None:
                if isinstance(field.default, Factory):
                    if not field.default.takes_self and field.default() == val:
                        assert field.name not in unstructured
                elif field.default == val:
                    assert field.name not in unstructured


def test_calling_back():
    """Calling unstructure_attrs_asdict from a hook should not override a manual hook."""
    converter = Converter()

    @attr.define
    class C:
        a: int = attr.ib(default=1)

    def handler(obj):
        return {
            "type_tag": obj.__class__.__name__,
            **converter.unstructure_attrs_asdict(obj),
        }

    converter.register_unstructure_hook(C, handler)

    inst = C()

    expected = {"type_tag": "C", "a": 1}

    unstructured1 = converter.unstructure(inst)
    unstructured2 = converter.unstructure(inst)

    assert unstructured1 == expected, repr(unstructured1)
    assert unstructured2 == unstructured1, repr(unstructured2)
