"""Tests for generated dict functions."""
from attr import Factory, fields
from attr._make import NOTHING
from hypothesis import assume, given
from hypothesis.strategies._internal.core import data, sampled_from

from cattr import Converter
from cattr.gen import (
    make_dict_structure_fn,
    make_dict_unstructure_fn,
    override,
)

from . import nested_classes, simple_classes
from .metadata import nested_typed_classes, simple_typed_classes


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
        cl, make_dict_unstructure_fn(cl, converter, omit_if_default=True)
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


@given(nested_classes | simple_classes())
def test_individual_overrides(cl_and_vals):
    """
    Test omitting default values on a per-class basis, but with individual
    overrides.
    """
    converter = Converter()
    cl, vals = cl_and_vals

    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr.default is not NOTHING:
            break
    else:
        assume(False)

    chosen = attr

    converter.register_unstructure_hook(
        cl,
        make_dict_unstructure_fn(
            cl,
            converter,
            omit_if_default=True,
            **{attr.name: override(omit_if_default=False)}
        ),
    )

    inst = cl(*vals)

    res = converter.unstructure(inst)

    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr is chosen:
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


@given(nested_typed_classes | simple_typed_classes())
def test_unmodified_generated_structuring(cl_and_vals):
    converter = Converter()
    cl, vals = cl_and_vals
    fn = make_dict_structure_fn(cl, converter)

    inst = cl(*vals)

    unstructured = converter.unstructure(inst)

    converter.register_structure_hook(cl, fn)

    res = converter.structure(unstructured, cl)

    assert inst == res


@given(simple_typed_classes(min_attrs=1), data())
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
