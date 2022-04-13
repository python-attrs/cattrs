"""Tests for auto-disambiguators."""
from typing import Any

import attr
import pytest
from attr import NOTHING
from hypothesis import HealthCheck, assume, given, settings

from cattrs.disambiguators import create_uniq_field_dis_func

from .untyped import simple_classes


def test_edge_errors():
    """Edge input cases cause errors."""

    @attr.s
    class A(object):
        pass

    with pytest.raises(ValueError):
        # Can't generate for only one class.
        create_uniq_field_dis_func(A)

    @attr.s
    class B(object):
        pass

    with pytest.raises(ValueError):
        # No fields on either class.
        create_uniq_field_dis_func(A, B)

    @attr.s
    class C(object):
        a = attr.ib()

    @attr.s
    class D(object):
        a = attr.ib()

    with pytest.raises(ValueError):
        # No unique fields on either class.
        create_uniq_field_dis_func(C, D)

    @attr.s
    class E:
        pass

    @attr.s
    class F:
        b = attr.ib(default=Any)

    with pytest.raises(ValueError):
        # no usable non-default attributes
        create_uniq_field_dis_func(E, F)


@given(simple_classes(defaults=False))
def test_fallback(cl_and_vals):
    """The fallback case works."""
    cl, vals, kwargs = cl_and_vals

    assume(attr.fields(cl))  # At least one field.

    @attr.s
    class A(object):
        pass

    fn = create_uniq_field_dis_func(A, cl)

    assert fn({}) is A
    assert fn(attr.asdict(cl(*vals, **kwargs))) is cl

    attr_names = {a.name for a in attr.fields(cl)}

    if "xyz" not in attr_names:
        fn({"xyz": 1}) is A  # Uses the fallback.


@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(simple_classes(), simple_classes())
def test_disambiguation(cl_and_vals_a, cl_and_vals_b):
    """Disambiguation should work when there are unique required fields."""
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, kwargs_b = cl_and_vals_b

    req_a = {a.name for a in attr.fields(cl_a)}
    req_b = {a.name for a in attr.fields(cl_b)}

    assume(len(req_a))
    assume(len(req_b))

    assume((req_a - req_b) or (req_b - req_a))
    for attr_name in req_a - req_b:
        assume(getattr(attr.fields(cl_a), attr_name).default is NOTHING)
    for attr_name in req_b - req_a:
        assume(getattr(attr.fields(cl_b), attr_name).default is NOTHING)

    fn = create_uniq_field_dis_func(cl_a, cl_b)

    assert fn(attr.asdict(cl_a(*vals_a, **kwargs_a))) is cl_a
