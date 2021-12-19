"""Tests for generated dict functions."""
import pytest
from attr import Factory, define, field
from attr._make import NOTHING
from hypothesis import assume, given
from hypothesis.strategies._internal.core import data, sampled_from

from cattr import Converter
from cattr._compat import adapted_fields, fields
from cattr.gen import (
    make_dict_structure_fn,
    make_dict_unstructure_fn,
    override,
)

from . import nested_classes, simple_classes
from .metadata import (
    nested_typed_classes,
    simple_typed_classes,
    simple_typed_dataclasses,
)


@given(nested_classes | simple_classes())
def test_unmodified_generated_unstructuring(cl_and_vals):
    converter = Converter()
    cl, vals = cl_and_vals
    fn = make_dict_unstructure_fn(cl, converter)

    inst = cl(*vals)

    res_expected = converter.unstructure(inst)

    converter.register_unstructure_hook(cl, fn)

    res_actual = converter.unstructure(inst)

    assert res_expected == res_actual


@given(nested_classes | simple_classes())
def test_nodefs_generated_unstructuring(cl_and_vals):
    """Test omitting default values on a per-attribute basis."""
    converter = Converter()
    cl, vals = cl_and_vals

    attr_is_default = False
    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr.default is not NOTHING:
            fn = make_dict_unstructure_fn(
                cl, converter, **{attr.name: override(omit_if_default=True)}
            )
            if attr.default == val:
                attr_is_default = True
            break
    else:
        assume(False)

    converter.register_unstructure_hook(cl, fn)

    inst = cl(*vals)

    res = converter.unstructure(inst)

    if attr_is_default:
        assert attr.name not in res


@given(nested_classes | simple_classes())
def test_nodefs_generated_unstructuring_cl(cl_and_vals):
    """Test omitting default values on a per-class basis."""
    converter = Converter()
    cl, vals = cl_and_vals

    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr.default is not NOTHING:
            break
    else:
        assume(False)

    converter.register_unstructure_hook(
        cl,
        make_dict_unstructure_fn(cl, converter, _cattrs_omit_if_default=True),
    )

    inst = cl(*vals)

    res = converter.unstructure(inst)

    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr.default is not NOTHING:
            if not isinstance(attr.default, Factory):
                if val == attr.default:
                    assert attr.name not in res
                else:
                    assert attr.name in res
            else:
                # The default is a factory, but might take self.
                if attr.default.takes_self:
                    if val == attr.default.factory(cl):
                        assert attr.name not in res
                    else:
                        assert attr.name in res
                else:
                    if val == attr.default.factory():
                        assert attr.name not in res
                    else:
                        assert attr.name in res


@given(nested_classes | simple_classes() | simple_typed_dataclasses())
def test_individual_overrides(cl_and_vals):
    """
    Test omitting default values on a per-class basis, but with individual
    overrides.
    """
    converter = Converter()
    cl, vals = cl_and_vals

    for attr, val in zip(adapted_fields(cl), vals):
        if attr.default is not NOTHING:
            break
    else:
        assume(False)

    chosen_name = attr.name

    converter.register_unstructure_hook(
        cl,
        make_dict_unstructure_fn(
            cl,
            converter,
            _cattrs_omit_if_default=True,
            **{attr.name: override(omit_if_default=False)}
        ),
    )

    inst = cl(*vals)

    res = converter.unstructure(inst)
    assert "Hyp" not in repr(res)
    assert "Factory" not in repr(res)

    for attr, val in zip(adapted_fields(cl), vals):
        if attr.name == chosen_name:
            assert attr.name in res
        elif attr.default is not NOTHING:
            if not isinstance(attr.default, Factory):
                if val == attr.default:
                    assert attr.name not in res
                else:
                    assert attr.name in res
            else:
                if attr.default.takes_self:
                    if val == attr.default.factory(inst):
                        assert attr.name not in res
                    else:
                        assert attr.name in res
                else:
                    if val == attr.default.factory():
                        assert attr.name not in res
                    else:
                        assert attr.name in res


@given(
    nested_typed_classes()
    | simple_typed_classes()
    | simple_typed_dataclasses()
)
def test_unmodified_generated_structuring(cl_and_vals):
    converter = Converter()
    cl, vals = cl_and_vals
    fn = make_dict_structure_fn(cl, converter)

    inst = cl(*vals)

    unstructured = converter.unstructure(inst)

    assert "Hyp" not in repr(unstructured)

    converter.register_structure_hook(cl, fn)

    res = converter.structure(unstructured, cl)

    assert inst == res


@given(
    simple_typed_classes(min_attrs=1) | simple_typed_dataclasses(min_attrs=1),
    data(),
)
def test_renaming(cl_and_vals, data):
    converter = Converter()
    cl, vals = cl_and_vals
    attrs = fields(cl)

    to_replace = data.draw(sampled_from(attrs))

    u_fn = make_dict_unstructure_fn(
        cl, converter, **{to_replace.name: override(rename="class")}
    )
    s_fn = make_dict_structure_fn(
        cl, converter, **{to_replace.name: override(rename="class")}
    )

    converter.register_structure_hook(cl, s_fn)
    converter.register_unstructure_hook(cl, u_fn)

    inst = cl(*vals)

    raw = converter.unstructure(inst)

    assert "class" in raw

    new_inst = converter.structure(raw, cl)

    assert inst == new_inst


def test_renaming_forbid_extra_keys():
    converter = Converter()

    @define
    class A:
        b: int
        c: str

    s_fn = make_dict_structure_fn(
        A, converter, c=override(rename="d"), _cattrs_forbid_extra_keys=True
    )

    converter.register_structure_hook(A, s_fn)

    new_inst = converter.structure({"b": 1, "d": "str"}, A)

    assert new_inst == A(1, "str")

    with pytest.raises(Exception):
        converter.structure({"b": 1, "c": "str"}, A)


def test_omitting():
    converter = Converter()

    @define
    class A:
        a: int
        b: int = field(init=False)

    converter.register_unstructure_hook(
        A, make_dict_unstructure_fn(A, converter, b=override(omit=True))
    )

    assert converter.unstructure(A(1)) == {"a": 1}


def test_omitting_structure():
    """Omitting fields works with generated structuring functions."""
    converter = Converter()

    @define
    class A:
        a: int
        b: int = field(init=False)
        c: int = 1

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A, converter, b=override(omit=True), c=override(omit=True)
        ),
    )

    # The 'c' parameter is ignored and the default is used instead.
    structured = converter.structure({"a": 1, "b": 2, "c": 3}, A)
    assert structured.a == 1
    assert structured.c == 1
    assert not hasattr(structured, "b")
