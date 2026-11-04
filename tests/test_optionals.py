from dataclasses import dataclass
from typing import Annotated, Any, NewType, Optional, Union

import pytest
from attrs import define, field, frozen

from cattrs import BaseConverter, Converter
from cattrs.errors import ClassValidationError
from cattrs.gen import make_dict_structure_fn, override

from ._compat import is_py310_plus


def test_newtype_optionals(genconverter):
    """Newtype optionals should work."""
    Foo = NewType("Foo", str)

    genconverter.register_unstructure_hook(Foo, lambda v: v.replace("foo", "bar"))

    @define
    class ModelWithFoo:
        total_foo: Foo
        maybe_foo: Optional[Foo]

    assert genconverter.unstructure(ModelWithFoo(Foo("foo"), Foo("is it a foo?"))) == {
        "total_foo": "bar",
        "maybe_foo": "is it a bar?",
    }


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
def test_newtype_modern_optionals(genconverter):
    """Newtype optionals should work."""
    Foo = NewType("Foo", str)

    genconverter.register_unstructure_hook(Foo, lambda v: v.replace("foo", "bar"))

    @define
    class ModelWithFoo:
        total_foo: Foo
        maybe_foo: Foo | None

    assert genconverter.unstructure(ModelWithFoo(Foo("foo"), Foo("is it a foo?"))) == {
        "total_foo": "bar",
        "maybe_foo": "is it a bar?",
    }


def test_optional_any(converter: Converter):
    """Unstructuring Any|None is equivalent to unstructuring as v.__class__."""

    @define
    class A:
        pass

    assert converter.unstructure(A(), Optional[Any]) == {}


def test_override_optional(converter: BaseConverter):
    """Optionals can be overridden using singledispatch."""

    @converter.register_structure_hook
    def _(val, _) -> Optional[int]:
        if val in ("", None):
            return None
        return int(val)

    assert converter.structure("", Optional[int]) is None
    assert converter.structure("1", Optional[int]) == 1

    @converter.register_unstructure_hook
    def _(val: Optional[int]) -> Any:
        if val in (None, 0):
            return None
        return val

    assert converter.unstructure(0, Optional[int]) is None
    assert converter.unstructure(5, Optional[int]) == 5


def test_missing_optional_without_default(converter):
    """Optional attributes without defaults are structured as None when missing."""

    @define
    class Dog:
        name: str
        nickname: Optional[str]

    assert converter.structure({"name": "Rex"}, Dog) == Dog("Rex", None)
    assert converter.structure({"name": "Spike", "nickname": "Carl"}, Dog) == Dog(
        "Spike", "Carl"
    )
    # An explicit None behaves the same as a missing key.
    assert converter.structure({"name": "Rex", "nickname": None}, Dog) == Dog(
        "Rex", None
    )


def test_missing_optional_between_required(converter):
    """Optional attributes without defaults may sit between required ones."""

    @frozen
    class C:
        a_float: float
        maybe_int: Optional[int]
        a_string: str

    assert converter.structure({"a_float": 0.1, "a_string": "hello"}, C) == C(
        0.1, None, "hello"
    )


def test_missing_optional_defaults_and_required(converter):
    """Defaults still win for missing keys, and required attributes still fail."""

    @define
    class C:
        req: str
        opt_default: Optional[int] = None
        opt_custom: Optional[str] = "custom default"
        plain_default: int = 42

    assert converter.structure({"req": "x"}, C) == C("x", None, "custom default", 42)
    # The error type depends on the structuring path, as before.
    with pytest.raises((ClassValidationError, KeyError, TypeError)):
        converter.structure({}, C)


def test_missing_union_with_none(converter):
    """Unions including None (of any arity) are structured as None when missing."""

    @define
    class C:
        multi: Union[bool, str, None]
        opt: Optional[int]

    converter.register_structure_hook(
        Union[bool, str, None],
        lambda v, _: v if v is None or isinstance(v, bool) else str(v),
    )

    assert converter.structure({}, C) == C(None, None)
    assert converter.structure({"multi": 5, "opt": 3}, C) == C("5", 3)


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
def test_missing_optional_pep604(genconverter):
    """PEP 604 unions including None are structured as None when missing."""

    @define
    class C:
        a: int | None
        b: str

    assert genconverter.structure({"b": "x"}, C) == C(None, "x")


def test_missing_optional_kw_only_and_alias(genconverter):
    """Missing optional kw-only and underscore attributes are structured as None."""

    @define
    class C:
        _private_opt: Optional[int]
        renamed: Optional[str] = field(kw_only=True)

    assert genconverter.structure({}, C) == C(None, renamed=None)
    assert genconverter.structure({"_private_opt": 3, "renamed": "a"}, C) == C(
        3, renamed="a"
    )

    aliased = Converter(use_alias=True)
    assert aliased.structure({}, C) == C(None, renamed=None)
    assert aliased.structure({"private_opt": 3, "renamed": "a"}, C) == C(3, renamed="a")


def test_missing_optional_rename():
    """Missing renamed optional attributes are structured as None."""

    @define
    class C:
        a: Optional[int]
        b: str

    converter = Converter()
    fn = make_dict_structure_fn(C, converter, a=override(rename="a_key"))

    assert fn({"b": "x"}, C) == C(None, "x")
    assert fn({"a_key": 1, "b": "x"}, C) == C(1, "x")


def test_missing_optional_init_false():
    """Missing optional init=False attributes are set to None if included."""

    @define
    class C:
        a: int
        opt: Optional[str] = field(init=False)

    converter = Converter()
    fn = make_dict_structure_fn(C, converter, _cattrs_include_init_false=True)

    assert fn({"a": 1}, C).opt is None
    assert fn({"a": 1, "opt": "v"}, C).opt == "v"
    # Without the flag, the attribute is not set at all, as before.
    assert not hasattr(converter.structure({"a": 1}, C), "opt")


def test_missing_optional_annotated(genconverter):
    """Missing annotated optional attributes are structured as None."""

    @define
    class C:
        a: Annotated[Optional[int], "note"]
        b: str

    assert genconverter.structure({"b": "x"}, C) == C(None, "x")


def test_missing_optional_dataclass(converter):
    """Missing optional dataclass fields without defaults are structured as None."""

    @dataclass
    class C:
        name: str
        nickname: Optional[str]

    assert converter.structure({"name": "Rex"}, C) == C("Rex", None)


def test_missing_optional_not_an_error():
    """A missing optional attribute does not contribute to the collected errors."""

    @define
    class C:
        opt: Optional[int]
        num: int

    converter = Converter(detailed_validation=True)
    with pytest.raises(ClassValidationError) as exc_info:
        converter.structure({"num": "not an int"}, C)

    assert len(exc_info.value.exceptions) == 1
