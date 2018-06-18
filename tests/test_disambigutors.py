"""Tests for auto-disambiguators."""
import attr
import pytest

from hypothesis import assume, given

from cattr.disambiguators import create_uniq_field_dis_func

from . import simple_classes


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


@given(simple_classes(defaults=False))
def test_fallback(cl_and_vals):
    """The fallback case works."""
    cl, vals = cl_and_vals

    assume(attr.fields(cl))  # At least one field.

    @attr.s
    class A(object):
        pass

    fn = create_uniq_field_dis_func(A, cl)

    assert fn({}) is A
    assert fn(attr.asdict(cl(*vals))) is cl

    attr_names = {a.name for a in attr.fields(cl)}

    if "xyz" not in attr_names:
        fn({"xyz": 1}) is A  # Uses the fallback.


@given(simple_classes(), simple_classes())
def test_disambiguation(cl_and_vals_a, cl_and_vals_b):
    """Disambiguation should work when there are unique fields."""
    cl_a, vals_a = cl_and_vals_a
    cl_b, vals_b = cl_and_vals_b

    req_a = {a.name for a in attr.fields(cl_a)}
    req_b = {a.name for a in attr.fields(cl_b)}

    assume(len(req_a))
    assume(len(req_b))

    assume((req_a - req_b) or (req_b - req_a))

    fn = create_uniq_field_dis_func(cl_a, cl_b)

    assert fn(attr.asdict(cl_a(*vals_a))) is cl_a
