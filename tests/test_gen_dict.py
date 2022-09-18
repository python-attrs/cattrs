"""Tests for generated dict functions."""
from typing import Dict, Type

import pytest
from attr import Factory, define, field
from attr._make import NOTHING
from hypothesis import assume, given
from hypothesis.strategies import data, just, one_of, sampled_from

from cattrs import BaseConverter, Converter
from cattrs._compat import adapted_fields, fields, is_py39_plus
from cattrs.errors import ClassValidationError, ForbiddenExtraKeysError
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

from .typed import nested_typed_classes, simple_typed_classes, simple_typed_dataclasses
from .untyped import nested_classes, simple_classes


@given(nested_classes | simple_classes())
def test_unmodified_generated_unstructuring(cl_and_vals):
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    fn = make_dict_unstructure_fn(cl, converter)

    inst = cl(*vals, **kwargs)

    res_expected = converter.unstructure(inst)

    converter.register_unstructure_hook(cl, fn)

    res_actual = converter.unstructure(inst)

    assert res_expected == res_actual


@given(nested_classes | simple_classes())
def test_nodefs_generated_unstructuring(cl_and_vals):
    """Test omitting default values on a per-attribute basis."""
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals

    attr_is_default = False
    for attr, val in zip([a for a in cl.__attrs_attrs__ if not a.kw_only], vals):
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

    inst = cl(*vals, **kwargs)

    res = converter.unstructure(inst)

    if attr_is_default:
        assert attr.name not in res


@given(one_of(just(BaseConverter), just(Converter)), nested_classes | simple_classes())
def test_nodefs_generated_unstructuring_cl(
    converter_cls: Type[BaseConverter], cl_and_vals
):
    """Test omitting default values on a per-class basis."""
    converter = converter_cls()
    cl, vals, kwargs = cl_and_vals

    for attr, val in zip(cl.__attrs_attrs__, vals):
        if attr.default is not NOTHING:
            break
    else:
        assume(False)

    converter.register_unstructure_hook(
        cl, make_dict_unstructure_fn(cl, converter, _cattrs_omit_if_default=True)
    )

    inst = cl(*vals, **kwargs)

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


@given(
    one_of(just(BaseConverter), just(Converter)),
    nested_classes | simple_classes() | simple_typed_dataclasses(),
)
def test_individual_overrides(converter_cls, cl_and_vals):
    """
    Test omitting default values on a per-class basis, but with individual
    overrides.
    """
    converter = converter_cls()
    cl, vals, kwargs = cl_and_vals

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

    inst = cl(*vals, **kwargs)

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
    cl_and_vals=nested_typed_classes()
    | simple_typed_classes()
    | simple_typed_dataclasses(),
    dv=...,
)
def test_unmodified_generated_structuring(cl_and_vals, dv: bool):
    converter = Converter(detailed_validation=dv)
    cl, vals, kwargs = cl_and_vals
    fn = make_dict_structure_fn(cl, converter, _cattrs_detailed_validation=dv)

    inst = cl(*vals, **kwargs)

    unstructured = converter.unstructure(inst)

    assert "Hyp" not in repr(unstructured)

    converter.register_structure_hook(cl, fn)

    res = converter.structure(unstructured, cl)

    assert inst == res


@given(
    simple_typed_classes(min_attrs=1) | simple_typed_dataclasses(min_attrs=1), data()
)
def test_renaming(cl_and_vals, data):
    converter = Converter()
    cl, vals, kwargs = cl_and_vals
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

    inst = cl(*vals, **kwargs)

    raw = converter.unstructure(inst)

    assert "class" in raw

    new_inst = converter.structure(raw, cl)

    assert inst == new_inst


def test_renaming_forbid_extra_keys():
    converter = BaseConverter()

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

    with pytest.raises(ClassValidationError) as cve:
        converter.structure({"b": 1, "c": "str"}, A)

    assert len(cve.value.exceptions) == 2
    assert isinstance(cve.value.exceptions[0], KeyError)
    assert isinstance(cve.value.exceptions[1], ForbiddenExtraKeysError)
    assert cve.value.exceptions[1].cl is A
    assert cve.value.exceptions[1].extra_fields == {"c"}


def test_omitting():
    converter = BaseConverter()

    @define
    class A:
        a: int
        b: int = field(init=False)

    converter.register_unstructure_hook(
        A, make_dict_unstructure_fn(A, converter, b=override(omit=True))
    )

    assert converter.unstructure(A(1)) == {"a": 1}


@pytest.mark.parametrize("extended_validation", [True, False])
def test_omitting_structure(extended_validation: bool):
    """Omitting fields works with generated structuring functions."""
    converter = BaseConverter()

    @define
    class A:
        a: int
        b: int = field(init=False)
        c: int = 1

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            b=override(omit=True),
            c=override(omit=True),
            _cattrs_extended_validation=extended_validation,
        ),
    )

    # The 'c' parameter is ignored and the default is used instead.
    structured = converter.structure({"a": 1, "b": 2, "c": 3}, A)
    assert structured.a == 1
    assert structured.c == 1
    assert not hasattr(structured, "b")


@pytest.mark.skipif(not is_py39_plus, reason="literals and annotated are 3.9+")
def test_type_names_with_quotes():
    """Types with quote characters in their reprs should work."""
    from typing import Annotated, Literal, Union

    converter = Converter()

    assert converter.structure({1: 1}, Dict[Annotated[int, "'"], int]) == {1: 1}

    converter.register_structure_hook_func(
        lambda t: t is Union[Literal["a", 2, 3], Literal[4]], lambda v, _: v
    )
    assert converter.structure(
        {2: "a"}, Dict[Union[Literal["a", 2, 3], Literal[4]], str]
    ) == {2: "a"}
