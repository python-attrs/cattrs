"""Tests for auto-disambiguators."""

from dataclasses import dataclass
from functools import partial
from typing import Literal, Union

import pytest
from attrs import NOTHING, asdict, define, field, fields
from hypothesis import HealthCheck, assume, given, settings

from cattrs import Converter
from cattrs.disambiguators import create_default_dis_func, is_supported_union
from cattrs.errors import StructureHandlerNotFoundError
from cattrs.gen import make_dict_structure_fn, override

from .untyped import simple_classes


def test_edge_errors():
    """Edge input cases cause errors."""
    c = Converter()

    @define
    class A:
        pass

    with pytest.raises(ValueError):
        # Can't generate for only one class.
        create_default_dis_func(c, A)

    with pytest.raises(ValueError):
        create_default_dis_func(c, A)

    @define
    class B:
        pass

    with pytest.raises(TypeError):
        # No fields on either class.
        create_default_dis_func(c, A, B)

    @define
    class C:
        a = field()

    @define
    class D:
        a = field()

    with pytest.raises(TypeError):
        # No unique fields on either class.
        create_default_dis_func(c, C, D)

    with pytest.raises(TypeError):
        # No discriminator candidates
        create_default_dis_func(c, C, D)

    @define
    class E:
        pass

    @define
    class F:
        b = None

    with pytest.raises(TypeError):
        # no usable non-default attributes
        create_default_dis_func(c, E, F)

    @define
    class G:
        x: Literal[1]

    @define
    class H:
        x: Literal[1]

    with pytest.raises(TypeError):
        # The discriminator chosen does not actually help
        create_default_dis_func(c, G, H)

    # Not an attrs class or dataclass
    class J:
        i: int

    with pytest.raises(StructureHandlerNotFoundError):
        c.get_structure_hook(Union[A, J])

    @define
    class K:
        x: Literal[2]

    fn = create_default_dis_func(c, G, K)
    with pytest.raises(ValueError):
        # The input should be a mapping
        fn([])

    # A normal class with a required attribute
    @define
    class L:
        b: str

    # C and L both have a required attribute, so there will be no fallback.
    fn = create_default_dis_func(c, C, L)
    with pytest.raises(ValueError):
        # We can't disambiguate based on this payload, so we error
        fn({"c": 1})

    # A has no attributes, so it ends up being the fallback
    fn = create_default_dis_func(c, A, C)
    with pytest.raises(ValueError):
        # The input should be a mapping
        fn([])


@given(simple_classes(defaults=False))
def test_fallback(cl_and_vals):
    """The fallback case works."""
    cl, vals, kwargs = cl_and_vals
    c = Converter()

    assume(fields(cl))  # At least one field.

    @define
    class A:
        pass

    fn = create_default_dis_func(c, A, cl)

    assert fn({}) is A
    assert fn(asdict(cl(*vals, **kwargs))) is cl

    assert fn({"xyz": 1}) is A  # Uses the fallback.


@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(simple_classes(), simple_classes())
def test_disambiguation(cl_and_vals_a, cl_and_vals_b):
    """Disambiguation should work when there are unique required fields."""
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, kwargs_b = cl_and_vals_b
    c = Converter()

    req_a = {a.name for a in fields(cl_a)}
    req_b = {a.name for a in fields(cl_b)}

    assume(len(req_a))
    assume(len(req_b))

    assume((req_a - req_b) or (req_b - req_a))
    for attr_name in req_a - req_b:
        assume(getattr(fields(cl_a), attr_name).default is NOTHING)
    for attr_name in req_b - req_a:
        assume(getattr(fields(cl_b), attr_name).default is NOTHING)

    fn = create_default_dis_func(c, cl_a, cl_b)

    assert fn(asdict(cl_a(*vals_a, **kwargs_a))) is cl_a


# not too sure of properties of `create_default_dis_func`
def test_disambiguate_from_discriminated_enum():
    c = Converter()

    # can it find any discriminator?
    @define
    class A:
        a: Literal[0]

    @define
    class B:
        a: Literal[1]

    fn = create_default_dis_func(c, A, B)
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

    fn = create_default_dis_func(c, C, D)
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

    fn = create_default_dis_func(c, E, F, G)
    assert fn({"op": 1}) is E
    assert fn({"op": 0, "t": "MESSAGE_CREATE"}) == Union[F, G]

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

    fn = create_default_dis_func(c, H, J, K)
    assert fn({"a": 1}) == Union[H, J]
    assert fn({"a": 0}) == Union[J, K]


def test_default_no_literals():
    """The default disambiguator can skip literals."""
    c = Converter()

    @define
    class A:
        a: Literal["a"] = "a"

    @define
    class B:
        a: Literal["b"] = "b"

    default = create_default_dis_func(c, A, B)  # Should work.
    assert default({"a": "a"}) is A

    with pytest.raises(TypeError):
        create_default_dis_func(c, A, B, use_literals=False)

    @define
    class C:
        b: int
        a: Literal["a"] = "a"

    @define
    class D:
        a: Literal["b"] = "b"

    default = create_default_dis_func(c, C, D)  # Should work.
    assert default({"a": "a"}) is C

    no_lits = create_default_dis_func(c, C, D, use_literals=False)
    assert no_lits({"a": "a", "b": 1}) is C
    assert no_lits({"a": "a"}) is D


def test_default_none():
    """The default disambiguator can handle `None`."""
    c = Converter()

    @define
    class A:
        a: int

    @define
    class B:
        b: str

    hook = c.get_structure_hook(Union[A, B, None])
    assert hook({"a": 1}, Union[A, B, None]) == A(1)
    assert hook(None, Union[A, B, None]) is None


def test_converter_no_literals(converter: Converter):
    """A converter can be configured to skip literals."""

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


def test_field_renaming(converter: Converter):
    """A renamed field properly disambiguates."""

    @define
    class A:
        a: int

    @define
    class B:
        a: int

    converter.register_structure_hook(
        B, make_dict_structure_fn(B, converter, a=override(rename="b"))
    )

    assert converter.structure({"a": 1}, Union[A, B]) == A(1)
    assert converter.structure({"b": 1}, Union[A, B]) == B(1)


def test_dataclasses(converter):
    """The default strategy works for dataclasses too."""

    @define
    class A:
        a: int

    @dataclass
    class B:
        b: int

    assert converter.structure({"a": 1}, Union[A, B]) == A(1)
    assert converter.structure({"b": 1}, Union[A, B]) == B(1)


def test_dataclasses_literals(converter):
    """The default strategy works for dataclasses too."""

    @define
    class A:
        a: Literal["a"] = "a"

    @dataclass
    class B:
        b: Literal["b"]

    assert converter.structure({"a": "a"}, Union[A, B]) == A()
    assert converter.structure({"b": "b"}, Union[A, B]) == B("b")
