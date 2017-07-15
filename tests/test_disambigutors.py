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
        a = attr.ib(default=0)

    with pytest.raises(ValueError):
        # Can't generate for only one class.
        create_uniq_field_dis_func(A)

    @attr.s
    class B(object):
        b = attr.ib(default=0)

    with pytest.raises(ValueError):
        # No required fields on either class.
        create_uniq_field_dis_func(A, B)


@given(simple_classes(defaults=False))
def test_fallback(cl_and_vals):
    """The fallback case works."""
    cl, vals = cl_and_vals

    assume(attr.fields(cl))  # At least one field.

    @attr.s
    class A(object):
        a = attr.ib(default=0)

    fn = create_uniq_field_dis_func(A, cl)

    assert fn({}) is A
    assert fn(attr.asdict(cl(*vals))) is cl
