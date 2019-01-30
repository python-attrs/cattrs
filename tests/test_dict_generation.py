"""Tests for generated dict functions."""
from attr._make import NOTHING
from cattr.generation import make_dict_unstructure_fn, override
from hypothesis import assume, given

from . import simple_classes, nested_classes


@given(nested_classes | simple_classes())
def test_unmodified_generated_unstructuring(converter, cl_and_vals):
    cl, vals = cl_and_vals
    fn = make_dict_unstructure_fn(cl, converter)

    inst = cl(*vals)

    res_expected = converter.unstructure(inst)

    converter.register_unstructure_hook(cl, fn)

    res_actual = converter.unstructure(inst)

    assert res_expected == res_actual


@given(nested_classes | simple_classes())
def test_nodefs_generated_unstructuring(converter, cl_and_vals):
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
