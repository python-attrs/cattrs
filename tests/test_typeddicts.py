"""Tests for TypedDict un/structuring."""

from datetime import datetime, timezone
from typing import Generic, NewType, TypedDict, TypeVar

import pytest
from attrs import NOTHING
from hypothesis import assume, given
from hypothesis.strategies import booleans
from pytest import raises
from typing_extensions import NotRequired, Required

from cattrs import BaseConverter, Converter, transform_error
from cattrs._compat import ExtensionsTypedDict, get_notrequired_base, is_generic
from cattrs.errors import (
    ClassValidationError,
    ForbiddenExtraKeysError,
    StructureHandlerNotFoundError,
)
from cattrs.gen import already_generating, override
from cattrs.gen._generics import generate_mapping
from cattrs.gen.typeddicts import (
    get_annots,
    make_dict_structure_fn,
    make_dict_unstructure_fn,
)

from ._compat import is_py311_plus
from .typeddicts import (
    gen_typeddict_attr_names,
    generic_typeddicts,
    simple_typeddicts,
    simple_typeddicts_with_extra_keys,
)


def test_gen_attr_names():
    """We can generate a lot of attribute names."""
    assert len(list(gen_typeddict_attr_names())) == 697

    # No duplicates!
    assert len(list(gen_typeddict_attr_names())) == len(set(gen_typeddict_attr_names()))


def mk_converter(detailed_validation: bool = True) -> Converter:
    """We can't use function-scoped fixtures with Hypothesis strats."""
    c = Converter(detailed_validation=detailed_validation)
    c.register_unstructure_hook(datetime, lambda d: d.timestamp())
    c.register_structure_hook(
        datetime, lambda d, _: datetime.fromtimestamp(d, tz=timezone.utc)
    )
    return c


def get_annot(t) -> dict:
    """Our version, handling type vars properly."""
    if is_generic(t):
        # This will have typevars.
        origin = getattr(t, "__origin__", None)
        if origin is not None:
            origin_annotations = get_annots(origin)
            args = t.__args__
            params = origin.__parameters__
            param_to_args = dict(zip(params, args))
            res = {}
            for k, v in origin_annotations.items():
                if (nrb := get_notrequired_base(v)) is not NOTHING:
                    res[k] = (
                        NotRequired[param_to_args[nrb]] if nrb in param_to_args else v
                    )
                else:
                    res[k] = param_to_args.get(v, v)
            return res

        # Origin is `None`, so this is a subclass for a generic typeddict.
        mapping = generate_mapping(t)
        res = {}
        for k, v in get_annots(t).items():
            if (nrb := get_notrequired_base(v)) is not NOTHING:
                res[k] = (
                    NotRequired[mapping[nrb.__name__]] if nrb.__name__ in mapping else v
                )
            else:
                res[k] = mapping.get(v.__name__, v)
        return res
    return get_annots(t)


@given(simple_typeddicts())
def test_simple_roundtrip(cls_and_instance) -> None:
    """Round-trips for simple classes work."""
    c = mk_converter()
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)

    if all(a is not datetime for _, a in get_annot(cls).items()):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@given(simple_typeddicts(total=False), booleans())
def test_simple_nontotal(cls_and_instance, detailed_validation: bool) -> None:
    """Non-total dicts work."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)

    if all(a is not datetime for _, a in get_annot(cls).items()):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@given(simple_typeddicts())
def test_int_override(cls_and_instance) -> None:
    """Overriding a base unstructure handler should work."""
    cls, instance = cls_and_instance

    assume(any(a is int for _, a in get_annot(cls).items()))
    assume(all(a is not datetime for _, a in get_annot(cls).items()))

    c = mk_converter()
    c.register_unstructure_hook(int, lambda i: i)
    unstructured = c.unstructure(instance, unstructure_as=cls)

    assert unstructured is not instance
    assert unstructured == instance


@given(simple_typeddicts_with_extra_keys(), booleans())
def test_extra_keys(
    cls_instance_extra: tuple[type, dict, set[str]], detailed_validation: bool
) -> None:
    """Extra keys are preserved."""
    cls, instance, extra = cls_instance_extra

    c = mk_converter(detailed_validation)

    unstructured = c.unstructure(instance, unstructure_as=cls)
    for k in extra:
        assert k in unstructured

    structured = c.structure(unstructured, cls)

    for k in extra:
        assert k in structured

    assert structured == instance


@pytest.mark.skipif(not is_py311_plus, reason="3.11+ only")
@given(generic_typeddicts(total=True), booleans())
def test_generics(
    cls_and_instance: tuple[type, dict], detailed_validation: bool
) -> None:
    """Generic TypedDicts work."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)
    assert not any(isinstance(v, datetime) for v in unstructured.values())

    if all(
        a not in (datetime, NotRequired[datetime]) for _, a in get_annot(cls).items()
    ):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@pytest.mark.skipif(not is_py311_plus, reason="3.11+ only")
@given(booleans())
def test_generics_with_unbound(detailed_validation: bool):
    """TypedDicts with unbound TypeVars work."""
    c = mk_converter(detailed_validation=detailed_validation)

    T = TypeVar("T")

    class GenericTypedDict(TypedDict, Generic[T]):
        a: T

    assert c.unstructure({"a": 1}, GenericTypedDict)

    with pytest.raises(StructureHandlerNotFoundError):
        # This doesn't work since we refuse the temptation to guess.
        c.structure({"a": 1}, GenericTypedDict)


@pytest.mark.skipif(not is_py311_plus, reason="3.11+ only")
@given(detailed_validation=...)
def test_deep_generics(detailed_validation: bool):
    c = mk_converter(detailed_validation=detailed_validation)

    Int = NewType("Int", int)

    c.register_unstructure_hook_func(lambda t: t is Int, lambda v: v - 1)

    T = TypeVar("T")
    T1 = TypeVar("T1")

    class GenericParent(TypedDict, Generic[T]):
        a: T

    class GenericChild(GenericParent[Int], Generic[T1]):
        b: T1

    assert c.unstructure({"b": 2, "a": 2}, GenericChild[Int]) == {"a": 1, "b": 1}


@given(simple_typeddicts(total=True, not_required=True), booleans())
def test_not_required(
    cls_and_instance: tuple[type, dict], detailed_validation: bool
) -> None:
    """NotRequired[] keys are handled."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)
    restructured = c.structure(unstructured, cls)

    assert restructured == instance


@given(simple_typeddicts(total=False, not_required=True), booleans())
def test_required(
    cls_and_instance: tuple[type, dict], detailed_validation: bool
) -> None:
    """Required[] keys are handled."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)
    restructured = c.structure(unstructured, cls)

    assert restructured == instance


@pytest.mark.skipif(not is_py311_plus, reason="Sigh")
def test_required_keys() -> None:
    """We don't support the full gamut of functionality on 3.9 and 3.10.

    When using `typing.TypedDict` we have only partial functionality;
    this test tests only a subset of this.
    """
    c = mk_converter()

    class Base(TypedDict, total=False):
        a: Required[datetime]

    class Sub(Base):
        b: int

    fn = make_dict_unstructure_fn(Sub, c)

    with raises(KeyError):
        # This needs to raise since 'a' is missing, and it's Required.
        fn({"b": 1})


@given(simple_typeddicts(min_attrs=1, total=True), booleans())
def test_omit(cls_and_instance: tuple[type, dict], detailed_validation: bool) -> None:
    """`override(omit=True)` works."""
    c = mk_converter(detailed_validation=detailed_validation)

    cls, instance = cls_and_instance
    key = next(iter(get_annot(cls)))
    c.register_unstructure_hook(
        cls,
        make_dict_unstructure_fn(
            cls,
            c,
            _cattrs_detailed_validation=detailed_validation,
            **{key: override(omit=True)},
        ),
    )

    unstructured = c.unstructure(instance, unstructure_as=cls)

    assert key not in unstructured

    unstructured[key] = c.unstructure(instance[key])
    restructured = c.structure(unstructured, cls)

    assert restructured == instance

    c.register_structure_hook(
        cls,
        make_dict_structure_fn(
            cls,
            c,
            _cattrs_detailed_validation=detailed_validation,
            **{key: override(omit=True)},
        ),
    )
    del unstructured[key]
    del instance[key]
    restructured = c.structure(unstructured, cls)

    assert restructured == instance


@given(simple_typeddicts(min_attrs=1, total=True, not_required=True), booleans())
def test_rename(cls_and_instance: tuple[type, dict], detailed_validation: bool) -> None:
    """`override(rename=...)` works."""
    c = mk_converter(detailed_validation=detailed_validation)

    cls, instance = cls_and_instance
    key = next(iter(get_annot(cls)))
    c.register_unstructure_hook(
        cls, make_dict_unstructure_fn(cls, c, **{key: override(rename="renamed")})
    )

    unstructured = c.unstructure(instance, unstructure_as=cls)

    assert key not in unstructured
    if key in instance:
        assert "renamed" in unstructured

    c.register_structure_hook(
        cls, make_dict_structure_fn(cls, c, **{key: override(rename="renamed")})
    )
    restructured = c.structure(unstructured, cls)

    assert restructured == instance


@given(simple_typeddicts(total=True), booleans())
def test_forbid_extra_keys(
    cls_and_instance: tuple[type, dict], detailed_validation: bool
) -> None:
    """Extra keys can be forbidden."""
    c = mk_converter(detailed_validation)

    cls, instance = cls_and_instance

    c.register_structure_hook(
        cls,
        make_dict_structure_fn(
            cls,
            c,
            _cattrs_detailed_validation=detailed_validation,
            _cattrs_forbid_extra_keys=True,
        ),
    )

    unstructured = c.unstructure(instance, unstructure_as=cls)

    structured = c.structure(unstructured, cls)
    assert structured == instance

    # An extra key will trigger the appropriate error.
    unstructured["test"] = 1

    if not detailed_validation:
        with raises(ForbiddenExtraKeysError):
            c.structure(unstructured, cls)
    else:
        with raises(ClassValidationError) as ctx:
            c.structure(unstructured, cls)

        assert repr(ctx.value) == repr(
            ClassValidationError(
                f"While structuring {cls.__name__}",
                [
                    ForbiddenExtraKeysError(
                        f"Extra fields in constructor for {cls.__name__}: test",
                        cls,
                        {"test"},
                    )
                ],
                cls,
            )
        )


class TypedDictA(ExtensionsTypedDict):
    b: "TypedDictB"


class TypedDictB(ExtensionsTypedDict):
    a: "TypedDictA"


@given(...)
def test_recursive_generation(detailed_validation: bool) -> None:
    """Generating recursive hooks works."""
    assert not hasattr(already_generating, "working_set")

    c = mk_converter(detailed_validation)

    assert c.unstructure({"a": {"b": {"a": {}}}}, TypedDictB) == {"a": {"b": {"a": {}}}}


def test_forwardref(genconverter: Converter):
    """TypedDicts have no resolve_class, so they're good candidate for forwardrefs."""

    class A(ExtensionsTypedDict):
        a: "int"

    genconverter.register_unstructure_hook(int, lambda v: v + 1)

    assert genconverter.unstructure({"a": 1}, A) == {"a": 2}


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

    class A(ExtensionsTypedDict):
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

    class A(ExtensionsTypedDict):
        a: int

    c.register_structure_hook(A, make_dict_structure_fn(A, c))

    c.structure({"a": 1, "b": 2}, A)


def test_detailed_validation_from_converter(converter: BaseConverter):
    """
    `detailed_validation` is taken from the converter by default.
    """

    class A(ExtensionsTypedDict):
        a: int

    converter.register_structure_hook(A, make_dict_structure_fn(A, converter))

    if converter.detailed_validation:
        with pytest.raises(ClassValidationError):
            converter.structure({"a": "a"}, A)
    else:
        with pytest.raises(ValueError):
            converter.structure({"a": "a"}, A)


def test_override_entire_hooks(converter: BaseConverter):
    """Overriding entire hooks works."""

    class A(ExtensionsTypedDict):
        a: int
        b: NotRequired[int]

    converter.register_structure_hook(
        A,
        make_dict_structure_fn(
            A,
            converter,
            a=override(struct_hook=lambda v, _: 1),
            b=override(struct_hook=lambda v, _: 2),
        ),
    )
    converter.register_unstructure_hook(
        A,
        make_dict_unstructure_fn(
            A,
            converter,
            a=override(unstruct_hook=lambda v: 1),
            b=override(unstruct_hook=lambda v: 2),
        ),
    )

    assert converter.unstructure({"a": 10, "b": 10}, A) == {"a": 1, "b": 2}
    assert converter.structure({"a": 10, "b": 10}, A) == {"a": 1, "b": 2}


def test_nondict_input():
    """Trying to structure typeddict from a non-dict raises the proper exception."""
    converter = Converter(detailed_validation=True)
    with raises(ClassValidationError) as exc:
        converter.structure(1, TypedDictA)

    assert transform_error(exc.value) == [
        "invalid type (expected a mapping, not int) @ $"
    ]

    with raises(ClassValidationError) as exc:
        converter.structure([1], TypedDictA)

    assert transform_error(exc.value) == [
        "invalid type (expected a mapping, not list) @ $"
    ]
