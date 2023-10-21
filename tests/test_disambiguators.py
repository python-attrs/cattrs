"""Tests for auto-disambiguators."""
from typing import Literal, Union

import pytest
from attrs import NOTHING, asdict, define, field, fields
from hypothesis import HealthCheck, assume, given, settings

from cattrs import Converter
from cattrs.disambiguators import (
    create_default_dis_func,
    create_uniq_field_dis_func,
    is_supported_union,
)

from .untyped import simple_classes


def test_edge_errors():
    """Edge input cases cause errors."""

    @define
    class A:
        pass

    with pytest.raises(ValueError):
        # Can't generate for only one class.
        create_uniq_field_dis_func(A)

    with pytest.raises(ValueError):
        create_default_dis_func(A)

    @define
    class B:
        pass

    with pytest.raises(ValueError):
        # No fields on either class.
        create_uniq_field_dis_func(A, B)

    with pytest.raises(ValueError):
        create_default_dis_func(A, B)

    @define
    class C:
        a = field()

    @define
    class D:
        a = field()

    with pytest.raises(ValueError):
        # No unique fields on either class.
        create_uniq_field_dis_func(C, D)

    with pytest.raises(ValueError):
        # No discriminator candidates
        create_default_dis_func(C, D)

    @define
    class E:
        pass

    @define
    class F:
        b = None

    with pytest.raises(ValueError):
        # no usable non-default attributes
        create_uniq_field_dis_func(E, F)

    @define
    class G:
        x: Literal[1]

    @define
    class H:
        x: Literal[1]

    with pytest.raises(ValueError):
        # The discriminator chosen does not actually help
        create_default_dis_func(C, D)


@given(simple_classes(defaults=False))
def test_fallback(cl_and_vals):
    """The fallback case works."""
    cl, vals, kwargs = cl_and_vals

    assume(fields(cl))  # At least one field.

    @define
    class A:
        pass

    fn = create_uniq_field_dis_func(A, cl)

    assert fn({}) is A
    assert fn(asdict(cl(*vals, **kwargs))) is cl

    attr_names = {a.name for a in fields(cl)}

    if "xyz" not in attr_names:
        assert fn({"xyz": 1}) is A  # Uses the fallback.


@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(simple_classes(), simple_classes())
def test_disambiguation(cl_and_vals_a, cl_and_vals_b):
    """Disambiguation should work when there are unique required fields."""
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, kwargs_b = cl_and_vals_b

    req_a = {a.name for a in fields(cl_a)}
    req_b = {a.name for a in fields(cl_b)}

    assume(len(req_a))
    assume(len(req_b))

    assume((req_a - req_b) or (req_b - req_a))
    for attr_name in req_a - req_b:
        assume(getattr(fields(cl_a), attr_name).default is NOTHING)
    for attr_name in req_b - req_a:
        assume(getattr(fields(cl_b), attr_name).default is NOTHING)

    fn = create_uniq_field_dis_func(cl_a, cl_b)

    assert fn(asdict(cl_a(*vals_a, **kwargs_a))) is cl_a


# not too sure of properties of `create_default_dis_func`
def test_disambiguate_from_discriminated_enum():
    # can it find any discriminator?
    @define
    class A:
        a: Literal[0]

    @define
    class B:
        a: Literal[1]

    fn = create_default_dis_func(A, B)
    assert fn({"a": 0}) is A
    assert fn({"a": 1}) is B

    # can it find the better discriminator?
    @define
    class C:
        a: Literal[0]
        b: Literal[1]

    @define
    class D:
        a: Literal[0]
        b: Literal[0]

    fn = create_default_dis_func(C, D)
    assert fn({"a": 0, "b": 1}) is C
    assert fn({"a": 0, "b": 0}) is D

    # can it handle multiple tiers of discriminators?
    # (example inspired by Discord's gateway's discriminated union)
    @define
    class E:
        op: Literal[1]

    @define
    class F:
        op: Literal[0]
        t: Literal["MESSAGE_CREATE"]

    @define
    class G:
        op: Literal[0]
        t: Literal["MESSAGE_UPDATE"]

    fn = create_default_dis_func(E, F, G)
    assert fn({"op": 1}) is E
    assert fn({"op": 0, "t": "MESSAGE_CREATE"}) is Union[F, G]

    # can it handle multiple literals?
    @define
    class H:
        a: Literal[1]

    @define
    class J:
        a: Literal[0, 1]

    @define
    class K:
        a: Literal[0]

    fn = create_default_dis_func(H, J, K)
    assert fn({"a": 1}) is Union[H, J]
    assert fn({"a": 0}) is Union[J, K]


def test_default_no_literals():
    """The default disambiguator can skip literals."""

    @define
    class A:
        a: Literal["a"] = "a"

    @define
    class B:
        a: Literal["b"] = "b"

    default = create_default_dis_func(A, B)  # Should work.
    assert default({"a": "a"}) is A

    with pytest.raises(ValueError):
        create_default_dis_func(A, B, use_literals=False)

    @define
    class C:
        b: int
        a: Literal["a"] = "a"

    @define
    class D:
        a: Literal["b"] = "b"

    default = create_default_dis_func(C, D)  # Should work.
    assert default({"a": "a"}) is C

    no_lits = create_default_dis_func(C, D, use_literals=False)
    assert no_lits({"a": "a", "b": 1}) is C
    assert no_lits({"a": "a"}) is D


def test_converter_no_literals(converter: Converter):
    """A converter can be configured to skip literals."""
    from functools import partial

    converter.register_structure_hook_factory(
        is_supported_union,
        partial(converter._gen_attrs_union_structure, use_literals=False),
    )

    @define
    class C:
        b: int
        a: Literal["a"] = "a"

    @define
    class D:
        a: Literal["b"] = "b"

    assert converter.structure({}, Union[C, D]) == D()
