"""Tests for generated dict functions."""

from typing import Dict, Type

import pytest
from attrs import NOTHING, Factory, define, field, frozen
from hypothesis import assume, given
from hypothesis.strategies import data, just, one_of, sampled_from

from cattrs import BaseConverter, Converter
from cattrs._compat import adapted_fields, fields
from cattrs.errors import ClassValidationError, ForbiddenExtraKeysError
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

from .typed import nested_typed_classes, simple_typed_classes, simple_typed_dataclasses
from .untyped import nested_classes, simple_classes


@given(nested_classes() | simple_classes())
def test_unmodified_generated_unstructuring(cl_and_vals):
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    fn = make_dict_unstructure_fn(cl, converter)

    inst = cl(*vals, **kwargs)

    res_expected = converter.unstructure(inst)

    converter.register_unstructure_hook(cl, fn)

    res_actual = converter.unstructure(inst)

    assert res_expected == res_actual


@given(nested_classes() | simple_classes())
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


@given(
    one_of(just(BaseConverter), just(Converter)), nested_classes() | simple_classes()
)
def test_nodefs_generated_unstructuring_cl(
    converter_cls: Type[BaseConverter], cl_and_vals
):
    """Test omitting default values on a per-class basis."""
    converter = converter_cls()
    cl, vals, kwargs = cl_and_vals

    for attr in cl.__attrs_attrs__:
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
                    # Our strategies can only produce these for now.
                    assert val == attr.default.factory(cl)
                    assert attr.name not in res
                else:
                    if val == attr.default.factory():
                        assert attr.name not in res
                    else:
                        assert attr.name in res


@given(
    one_of(just(BaseConverter), just(Converter)),
    nested_classes() | simple_classes() | simple_typed_dataclasses(),
)
def test_individual_overrides(converter_cls, cl_and_vals):
    """
    Test omitting default values on a per-class basis, but with individual
    overrides.
    """
    converter = converter_cls()
    cl, vals, kwargs = cl_and_vals

    for attr in adapted_fields(cl):
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
            **{attr.name: override(omit_if_default=False)},
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
                    assert attr.name not in res
                else:
                    if val == attr.default.factory():
                        assert attr.name not in res
                    else:
                        assert attr.name in res


@given(
    cl_and_vals=nested_typed_classes(allow_nan=False)
    | simple_typed_classes(allow_nan=False)
    | simple_typed_dataclasses(allow_nan=False),
    dv=...,
)
def test_unmodified_generated_structuring(cl_and_vals, dv: bool):
    converter = Converter(detailed_validation=dv)
    cl, vals, kwargs = cl_and_vals
    fn = make_dict_structure_fn(cl, converter, _cattrs_detailed_validation=dv)
    assert fn.overrides == {}

    inst = cl(*vals, **kwargs)

    unstructured = converter.unstructure(inst)

    assert "Hyp" not in repr(unstructured)

    converter.register_structure_hook(cl, fn)

    res = converter.structure(unstructured, cl)

    assert inst == res


@given(
    simple_typed_classes(min_attrs=1, allow_nan=False)
    | simple_typed_dataclasses(min_attrs=1, allow_nan=False),
    data(),
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
    assert s_fn.overrides == {to_replace.name: override(rename="class")}
    assert u_fn.overrides == {to_replace.name: override(rename="class")}

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


def test_omitting(converter: BaseConverter):
    """Omitting works."""

    @define
    class A:
        a: int
        b: int = field(init=False)

    converter.register_unstructure_hook(
        A, make_dict_unstructure_fn(A, converter, b=override(omit=True))
    )

    assert converter.unstructure(A(1)) == {"a": 1}


def test_omitting_none(converter: BaseConverter):
    """Omitting works properly with None."""

    @define
    class A:
        a: int
        b: int = field(init=False)

    converter.register_unstructure_hook(
        A, make_dict_unstructure_fn(A, converter, a=override(), b=override())
    )

    assert converter.unstructure(A(1)) == {"a": 1}

    converter.register_structure_hook(
        A, make_dict_structure_fn(A, converter, a=override(), b=override())
    )

    assert converter.structure({"a": 2}, A).a == 2
    assert not hasattr(converter.structure({"a": 2}, A), "b")


@pytest.mark.parametrize("detailed_validation", [True, False])
def test_omitting_structure(detailed_validation: bool):
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
            _cattrs_detailed_validation=detailed_validation,
        ),
    )

    # The 'c' parameter is ignored and the default is used instead.
    structured = converter.structure({"a": 1, "b": 2, "c": 3}, A)
    assert structured.a == 1
    assert structured.c == 1
    assert not hasattr(structured, "b")


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


def test_overriding_struct_hook(converter: BaseConverter) -> None:
    """Overriding structure hooks works."""
    from math import ceil

    @define
    class A:
        a: int
        b: str
        c: int = 0

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            a=override(struct_hook=lambda v, _: ceil(v)),
            c=override(struct_hook=lambda v, _: ceil(v)),
            _cattrs_detailed_validation=converter.detailed_validation,
        ),
    )

    assert converter.structure({"a": 0.5, "b": 1, "c": 0.5}, A) == A(1, "1", 1)


def test_overriding_unstruct_hook(converter: BaseConverter) -> None:
    """Overriding unstructure hooks works."""

    @define
    class A:
        a: int
        b: str

    converter.register_unstructure_hook(
        A,
        make_dict_unstructure_fn(
            A, converter, a=override(unstruct_hook=lambda v: v + 1)
        ),
    )

    assert converter.unstructure(A(1, "")) == {"a": 2, "b": ""}


def test_alias_keys(converter: BaseConverter) -> None:
    """Alias keys work."""

    @define
    class A:
        _a: int
        b: int = field(alias="aliased")
        c: int = field(alias="also_aliased", default=3)
        d: int = field(alias="d_aliased", default=5)

    converter.register_unstructure_hook(
        A,
        make_dict_unstructure_fn(
            A,
            converter,
            _cattrs_use_alias=True,
            c=override(omit=True),
            d=override(rename="d_renamed"),
        ),
    )

    assert converter.unstructure(A(1, 2, 3, 4)) == {
        "a": 1,
        "aliased": 2,
        "d_renamed": 4,
    }

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            _cattrs_use_alias=True,
            _cattrs_detailed_validation=converter.detailed_validation,
            c=override(omit=True),
            d=override(rename="d_renamed"),
        ),
    )

    assert converter.structure({"a": 1, "aliased": 2, "d_renamed": 4}, A) == A(
        1, 2, 3, 4
    )


def test_init_false(converter: BaseConverter) -> None:
    """By default init=False keys are ignored."""

    @define
    class A:
        a: int
        b: int = field(init=False)
        _c: int = field(init=False)
        d: int = field(init=False, default=4)

    converter.register_unstructure_hook(A, make_dict_unstructure_fn(A, converter))

    a = A(1)
    a.b = 2
    a._c = 3

    assert converter.unstructure(a) == {"a": 1}

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A, converter, _cattrs_detailed_validation=converter.detailed_validation
        ),
    )

    structured = converter.structure({"a": 1}, A)

    assert not hasattr(structured, "b")
    assert not hasattr(structured, "_c")
    assert structured.d == 4
    assert structured.a == 1


def test_init_false_overridden(converter: BaseConverter) -> None:
    """init=False handling can be overriden."""

    @frozen
    class Inner:
        a: int

    @define
    class A:
        a: int
        b: int = field(init=False)
        _c: int = field(init=False)
        d: Inner = field(init=False)
        e: int = field(init=False, default=4)
        f: Inner = field(init=False, default=Inner(1))

    converter.register_unstructure_hook(
        A, make_dict_unstructure_fn(A, converter, _cattrs_include_init_false=True)
    )

    a = A(1)
    a.b = 2
    a._c = 3
    a.d = Inner(4)

    assert converter.unstructure(a) == {
        "a": 1,
        "b": 2,
        "_c": 3,
        "d": {"a": 4},
        "e": 4,
        "f": {"a": 1},
    }

    converter.register_structure_hook(
        A, make_dict_structure_fn(A, converter, _cattrs_include_init_false=True)
    )

    structured = converter.structure({"a": 1, "b": 2, "_c": 3, "d": {"a": 1}}, A)
    assert structured.b == 2
    assert structured._c == 3
    assert structured.d == Inner(1)
    assert structured.e == 4
    assert structured.f == Inner(1)

    structured = converter.structure(
        {"a": 1, "b": 2, "_c": 3, "d": {"a": 5}, "e": -4, "f": {"a": 2}}, A
    )
    assert structured.b == 2
    assert structured._c == 3
    assert structured.d == Inner(5)
    assert structured.e == -4
    assert structured.f == Inner(2)


def test_init_false_field_override(converter: BaseConverter) -> None:
    """init=False handling can be overriden on a per-field basis."""

    @define
    class A:
        a: int
        b: int = field(init=False)
        _c: int = field(init=False)
        d: int = field(init=False, default=4)

    converter.register_unstructure_hook(
        A,
        make_dict_unstructure_fn(
            A,
            converter,
            b=override(omit=False),
            _c=override(omit=False),
            d=override(omit=False),
        ),
    )

    a = A(1)
    a.b = 2
    a._c = 3

    assert converter.unstructure(a) == {"a": 1, "b": 2, "_c": 3, "d": 4}

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            b=override(omit=False),
            _c=override(omit=False),
            d=override(omit=False),
            _cattrs_detailed_validation=converter.detailed_validation,
        ),
    )

    structured = converter.structure({"a": 1, "b": 2, "_c": 3}, A)
    assert structured.b == 2
    assert structured._c == 3
    assert structured.d == 4

    structured = converter.structure({"a": 1, "b": 2, "_c": 3, "d": -4}, A)
    assert structured.b == 2
    assert structured._c == 3
    assert structured.d == -4


def test_init_false_no_structure_hook(converter: BaseConverter):
    """init=False attributes with converters and `prefer_attrs_converters` work."""

    @define
    class A:
        a: int = field(converter=int, init=False)
        b: int = field(converter=int, init=False, default=5)

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            _cattrs_prefer_attrib_converters=True,
            _cattrs_include_init_false=True,
        ),
    )

    res = A()
    res.a = 5

    assert converter.structure({"a": "5"}, A) == res


@given(forbid_extra_keys=..., detailed_validation=...)
def test_forbid_extra_keys_from_converter(
    forbid_extra_keys: bool, detailed_validation: bool
):
    """
    `forbid_extra_keys` is taken from the converter by default.
    """
    c = Converter(
        forbid_extra_keys=forbid_extra_keys, detailed_validation=detailed_validation
    )

    @define
    class A:
        a: int

    c.register_structure_hook(A, make_dict_structure_fn(A, c))

    if forbid_extra_keys:
        with pytest.raises((ForbiddenExtraKeysError, ClassValidationError)):
            c.structure({"a": 1, "b": 2}, A)
    else:
        c.structure({"a": 1, "b": 2}, A)


@given(detailed_validation=...)
def test_forbid_extra_keys_from_baseconverter(detailed_validation: bool):
    """
    `forbid_extra_keys` is taken from the converter by default.

    BaseConverter should default to False.
    """
    c = BaseConverter(detailed_validation=detailed_validation)

    @define
    class A:
        a: int

    c.register_structure_hook(A, make_dict_structure_fn(A, c))

    c.structure({"a": 1, "b": 2}, A)


def test_detailed_validation_from_converter(converter: BaseConverter):
    """
    `detailed_validation` is taken from the converter by default.
    """

    @define
    class A:
        a: int

    converter.register_structure_hook(A, make_dict_structure_fn(A, converter))

    if converter.detailed_validation:
        with pytest.raises(ClassValidationError):
            converter.structure({"a": "a"}, A)
    else:
        with pytest.raises(ValueError):
            converter.structure({"a": "a"}, A)


@given(prefer=..., dv=...)
def test_prefer_converters_from_converter(prefer: bool, dv: bool):
    """
    `prefer_attrs_converters` is taken from the converter by default.
    """

    @define
    class A:
        a: int = field(converter=lambda x: x + 1)
        b: int = field(converter=lambda x: x + 1, default=5)

    converter = BaseConverter(prefer_attrib_converters=prefer)
    converter.register_structure_hook(int, lambda x, _: x + 1)
    converter.register_structure_hook(
        A, make_dict_structure_fn(A, converter, _cattrs_detailed_validation=dv)
    )

    if prefer:
        assert converter.structure({"a": 1, "b": 2}, A).a == 2
        assert converter.structure({"a": 1, "b": 2}, A).b == 3
    else:
        assert converter.structure({"a": 1}, A).a == 3


def test_fields_exception():
    """fields() raises on a non-attrs, non-dataclass class."""
    with pytest.raises(Exception):  # noqa: B017
        fields(int)
