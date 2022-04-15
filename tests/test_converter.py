"""Test both structuring and unstructuring."""
from typing import (
    FrozenSet,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import attr
import pytest
from attr import Factory, define, fields, make_class
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import booleans, just, lists, one_of, sampled_from

from cattrs import Converter, UnstructureStrategy
from cattrs._compat import is_py39_plus, is_py310_plus
from cattrs.errors import ClassValidationError, ForbiddenExtraKeysError
from cattrs.gen import make_dict_structure_fn, override

from .typed import (
    nested_typed_classes,
    simple_typed_attrs,
    simple_typed_classes,
    simple_typed_dataclasses,
)

unstructure_strats = one_of(just(s) for s in UnstructureStrategy)


@given(simple_typed_classes() | simple_typed_dataclasses(), booleans())
def test_simple_roundtrip(cls_and_vals, detailed_validation):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    converter = Converter(detailed_validation=detailed_validation)
    cl, vals, kwargs = cls_and_vals
    inst = cl(*vals, **kwargs)
    unstructured = converter.unstructure(inst)
    assert "Hyp" not in repr(unstructured)
    assert inst == converter.structure(unstructured, cl)


@given(
    simple_typed_classes(kw_only=False, newtypes=False)
    | simple_typed_dataclasses(newtypes=False),
    booleans(),
)
def test_simple_roundtrip_tuple(cls_and_vals, dv: bool):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    converter = Converter(
        unstruct_strat=UnstructureStrategy.AS_TUPLE, detailed_validation=dv
    )
    cl, vals, _ = cls_and_vals
    inst = cl(*vals)
    unstructured = converter.unstructure(inst)
    assert "Hyp" not in repr(unstructured)
    assert inst == converter.structure(unstructured, cl)


@given(simple_typed_attrs(defaults=True))
def test_simple_roundtrip_defaults(attr_and_vals):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    a, _ = attr_and_vals
    cl = make_class("HypClass", {"a": a})
    converter = Converter()
    inst = cl()
    assert converter.unstructure(converter.structure({}, cl)) == converter.unstructure(
        inst
    )
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(simple_typed_attrs(defaults=True, kw_only=False, newtypes=False))
def test_simple_roundtrip_defaults_tuple(attr_and_vals):
    """
    Simple classes with metadata can be unstructured and restructured.
    """
    a, _ = attr_and_vals
    cl = make_class("HypClass", {"a": a})
    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
    inst = cl()
    assert converter.unstructure(converter.structure({}, cl)) == converter.unstructure(
        inst
    )
    assert inst == converter.structure(converter.unstructure(inst), cl)


@given(
    simple_typed_classes(newtypes=False) | simple_typed_dataclasses(newtypes=False),
    unstructure_strats,
)
def test_simple_roundtrip_with_extra_keys_forbidden(cls_and_vals, strat):
    """
    Simple classes can be unstructured and restructured with forbid_extra_keys=True.
    """
    converter = Converter(unstruct_strat=strat, forbid_extra_keys=True)
    cl, vals, kwargs = cls_and_vals
    assume(strat is UnstructureStrategy.AS_DICT or not kwargs)
    inst = cl(*vals, **kwargs)
    unstructured = converter.unstructure(inst)
    assert "Hyp" not in repr(unstructured)
    assert inst == converter.structure(unstructured, cl)


@given(simple_typed_classes() | simple_typed_dataclasses())
def test_forbid_extra_keys(cls_and_vals):
    """
    Restructuring fails when extra keys are present (when configured)
    """
    converter = Converter(forbid_extra_keys=True)
    cl, vals, kwargs = cls_and_vals
    inst = cl(*vals, **kwargs)
    unstructured = converter.unstructure(inst)
    bad_key = list(unstructured)[0] + "A" if unstructured else "Hyp"
    while bad_key in unstructured:
        bad_key += "A"
    unstructured[bad_key] = 1
    with pytest.raises(ClassValidationError) as cve:
        converter.structure(unstructured, cl)

    assert len(cve.value.exceptions) == 1
    assert isinstance(cve.value.exceptions[0], ForbiddenExtraKeysError)
    assert cve.value.exceptions[0].cl is cl
    assert cve.value.exceptions[0].extra_fields == {bad_key}


@given(simple_typed_attrs(defaults=True))
def test_forbid_extra_keys_defaults(attr_and_vals):
    """
    Restructuring fails when a dict key is renamed (if forbid_extra_keys set)
    """
    a, _ = attr_and_vals
    cl = make_class("HypClass", {"a": a})
    converter = Converter(forbid_extra_keys=True)
    inst = cl()
    unstructured = converter.unstructure(inst)
    unstructured["aa"] = unstructured.pop("a")
    with pytest.raises(ClassValidationError) as cve:
        converter.structure(unstructured, cl)

    assert len(cve.value.exceptions) == 1
    assert isinstance(cve.value.exceptions[0], ForbiddenExtraKeysError)
    assert cve.value.exceptions[0].cl is cl
    assert cve.value.exceptions[0].extra_fields == {"aa"}


def test_forbid_extra_keys_nested_override():
    @attr.s
    class C:
        a = attr.ib(type=int, default=1)

    @attr.s
    class A:
        c = attr.ib(type=C)
        a = attr.ib(type=int, default=2)

    converter = Converter(forbid_extra_keys=True)
    unstructured = {"a": 3, "c": {"a": 4}}
    # at this point, structuring should still work
    converter.structure(unstructured, A)
    # if we break it in the subclass, we need it to raise
    unstructured["c"]["aa"] = 5
    with pytest.raises(ClassValidationError) as cve:
        converter.structure(unstructured, A)

    assert len(cve.value.exceptions) == 1
    assert isinstance(cve.value.exceptions[0], ClassValidationError)
    assert len(cve.value.exceptions[0].exceptions) == 1
    assert isinstance(cve.value.exceptions[0].exceptions[0], ForbiddenExtraKeysError)
    assert cve.value.exceptions[0].exceptions[0].cl is C
    assert cve.value.exceptions[0].exceptions[0].extra_fields == {"aa"}

    # we can "fix" that by disabling forbid_extra_keys on the subclass
    hook = make_dict_structure_fn(C, converter, _cattrs_forbid_extra_keys=False)
    converter.register_structure_hook(C, hook)
    converter.structure(unstructured, A)
    # but we should still raise at the top level
    unstructured["b"] = 6
    with pytest.raises(ClassValidationError) as cve:
        converter.structure(unstructured, A)

    assert len(cve.value.exceptions) == 1
    assert isinstance(cve.value.exceptions[0], ForbiddenExtraKeysError)
    assert cve.value.exceptions[0].cl is A
    assert cve.value.exceptions[0].extra_fields == {"b"}


@given(nested_typed_classes(defaults=True, min_attrs=1), booleans())
def test_nested_roundtrip(cls_and_vals, omit_if_default):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter = Converter(omit_if_default=omit_if_default)
    cl, vals, kwargs = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals, **kwargs)
    unstructured = converter.unstructure(inst)
    assert inst == converter.structure(unstructured, cl)


@given(
    nested_typed_classes(defaults=True, min_attrs=1, kw_only=False, newtypes=False),
    booleans(),
)
def test_nested_roundtrip_tuple(cls_and_vals, omit_if_default: bool):
    """
    Nested classes with metadata can be unstructured and restructured.
    """
    converter = Converter(
        unstruct_strat=UnstructureStrategy.AS_TUPLE, omit_if_default=omit_if_default
    )
    cl, vals, _ = cls_and_vals
    # Vals are a tuple, convert into a dictionary.
    inst = cl(*vals)
    unstructured = converter.unstructure(inst)
    assert inst == converter.structure(unstructured, cl)


@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(
    simple_typed_classes(defaults=False, newtypes=False),
    simple_typed_classes(defaults=False, newtypes=False),
    unstructure_strats,
)
def test_union_field_roundtrip(cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter = Converter(unstruct_strat=strat)
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, _, _ = cl_and_vals_b
    assume(strat is UnstructureStrategy.AS_DICT or not kwargs_a)
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    assume(len(a_field_names) > len(common_names))

    @attr.s
    class C(object):
        a = attr.ib(type=Union[cl_a, cl_b])

    inst = C(a=cl_a(*vals_a, **kwargs_a))

    if strat is UnstructureStrategy.AS_DICT:
        unstructured = converter.unstructure(inst)
        assert inst == converter.structure(converter.unstructure(unstructured), C)
    else:
        # Our disambiguation functions only support dictionaries for now.
        with pytest.raises(ValueError):
            converter.structure(converter.unstructure(inst), C)

        def handler(obj, _):
            return converter.structure(obj, cl_a)

        converter.register_structure_hook(Union[cl_a, cl_b], handler)
        unstructured = converter.unstructure(inst)
        assert inst == converter.structure(unstructured, C)


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow])
@given(
    simple_typed_classes(defaults=False, newtypes=False),
    simple_typed_classes(defaults=False, newtypes=False),
    unstructure_strats,
)
def test_310_union_field_roundtrip(cl_and_vals_a, cl_and_vals_b, strat):
    """
    Classes with union fields can be unstructured and structured.
    """
    converter = Converter(unstruct_strat=strat)
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, _, _ = cl_and_vals_b
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
        unstructured = converter.unstructure(inst)
        assert inst == converter.structure(converter.unstructure(unstructured), C)
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
    cl, vals, kwargs = cl_and_vals

    @attr.s
    class C(object):
        a = attr.ib(type=Optional[cl])

    inst = C(a=cl(*vals, **kwargs))
    assert inst == converter.structure(converter.unstructure(inst), C)

    inst = C(a=None)
    unstructured = converter.unstructure(inst)

    assert inst == converter.structure(unstructured, C)


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
@given(simple_typed_classes(defaults=False))
def test_310_optional_field_roundtrip(cl_and_vals):
    """
    Classes with optional fields can be unstructured and structured.
    """
    converter = Converter()
    cl, vals, kwargs = cl_and_vals

    @define
    class C:
        a: cl | None

    inst = C(a=cl(*vals, **kwargs))
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
    cl, vals, kwargs = cl_and_vals

    @attr.s
    class C(object):
        a: int = attr.ib(default=1)
        b: cl = attr.ib(factory=lambda: cl(*vals, **kwargs))

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
    cl, vals, kwargs = cl_and_vals

    inst = cl(*vals, **kwargs)
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


def test_overriding_generated_unstructure():
    """Test overriding a generated unstructure hook works."""
    converter = Converter()

    @attr.define
    class Inner:
        a: int

    @attr.define
    class Outer:
        i: Inner

    inst = Outer(Inner(1))
    converter.unstructure(inst)

    converter.register_unstructure_hook(Inner, lambda _: {"a": 2})

    r = converter.structure(converter.unstructure(inst), Outer)
    assert r.i.a == 2


def test_overriding_generated_unstructure_hook_func():
    """Test overriding a generated unstructure hook works."""
    converter = Converter()

    @attr.define
    class Inner:
        a: int

    @attr.define
    class Outer:
        i: Inner

    inst = Outer(Inner(1))
    converter.unstructure(inst)

    converter.register_unstructure_hook_func(lambda t: t is Inner, lambda _: {"a": 2})

    r = converter.structure(converter.unstructure(inst), Outer)
    assert r.i.a == 2


def test_overriding_generated_structure():
    """Test overriding a generated structure hook works."""
    converter = Converter()

    @attr.define
    class Inner:
        a: int

    @attr.define
    class Outer:
        i: Inner

    inst = Outer(Inner(1))
    raw = converter.unstructure(inst)
    converter.structure(raw, Outer)

    converter.register_structure_hook(Inner, lambda p, _: Inner(p["a"] + 1))

    r = converter.structure(raw, Outer)
    assert r.i.a == 2


def test_overriding_generated_structure_hook_func():
    """Test overriding a generated structure hook works."""
    converter = Converter()

    @attr.define
    class Inner:
        a: int

    @attr.define
    class Outer:
        i: Inner

    inst = Outer(Inner(1))
    raw = converter.unstructure(inst)
    converter.structure(raw, Outer)

    converter.register_structure_hook_func(
        lambda t: t is Inner, lambda p, _: Inner(p["a"] + 1)
    )

    r = converter.structure(raw, Outer)
    assert r.i.a == 2


@given(
    lists(simple_typed_classes(frozen=True), min_size=1),
    sampled_from(
        [
            (tuple, Tuple),
            (tuple, tuple),
            (list, list),
            (list, List),
            (set, Set),
            (set, set),
            (frozenset, frozenset),
            (frozenset, FrozenSet),
            (list, MutableSequence),
            (tuple, Sequence),
        ]
        if is_py39_plus
        else [
            (tuple, Tuple),
            (list, List),
            (set, Set),
            (frozenset, FrozenSet),
            (list, MutableSequence),
            (tuple, Sequence),
        ]
    ),
)
def test_seq_of_simple_classes_unstructure(cls_and_vals, seq_type_and_annotation):
    """Dumping a sequence of primitives is a simple copy operation."""
    converter = Converter()

    test_val = ("test", 1)

    for cl, _, _ in cls_and_vals:
        converter.register_unstructure_hook(cl, lambda _: test_val)
        break  # Just register the first class.

    seq_type, annotation = seq_type_and_annotation
    inputs = seq_type(cl(*vals, **kwargs) for cl, vals, kwargs in cls_and_vals)
    outputs = converter.unstructure(
        inputs,
        unstructure_as=annotation[cl]
        if annotation not in (Tuple, tuple)
        else annotation[cl, ...],
    )
    assert all(e == test_val for e in outputs)


@pytest.mark.skipif(not is_py39_plus, reason="3.9+ only")
def test_annotated_attrs():
    """Annotation support works for attrs classes."""
    from typing import Annotated

    converter = Converter()

    @attr.define
    class Inner:
        a: int

    @attr.define
    class Outer:
        i: Annotated[Inner, "test"]  # noqa
        j: list[Annotated[Inner, "test"]]  # noqa

    orig = Outer(Inner(1), [Inner(1)])
    raw = converter.unstructure(orig)

    assert raw == {"i": {"a": 1}, "j": [{"a": 1}]}

    structured = converter.structure(raw, Outer)
    assert structured == orig

    # Now register a hook and rerun the test.
    converter.register_unstructure_hook(Inner, lambda v: {"a": 2})

    raw = converter.unstructure(Outer(Inner(1), [Inner(1)]))

    assert raw == {"i": {"a": 2}, "j": [{"a": 2}]}

    structured = converter.structure(raw, Outer)
    assert structured == Outer(Inner(2), [Inner(2)])
