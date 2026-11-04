"""Tests for the cattrs.v framework."""

import pickle
from typing import (
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
)

from attrs import Factory, define, field
from pytest import fixture, mark, raises

from cattrs import Converter, TypeValidationNote, transform_error
from cattrs._compat import Mapping
from cattrs.errors import ClassValidationError, IterableValidationError
from cattrs.gen import make_dict_structure_fn
from cattrs.v import format_exception


@fixture
def c() -> Converter:
    """We need only converters with detailed_validation=True."""
    return Converter(detailed_validation=True)


@mark.parametrize("cl", [int, float])
def test_primitive_errors(c: Converter, cl: type) -> None:
    """Top-level primitive errors include the target type."""
    with raises(ValueError) as exc:
        c.structure("x", cl)

    assert transform_error(exc.value) == [
        f"invalid value for type, expected {cl.__name__} @ $"
    ]


def test_custom_error_fn_primitive(c: Converter) -> None:
    """Custom formatters receive the target type for primitive errors."""
    with raises(ValueError) as exc:
        c.structure("x", int)

    def my_format(error, type):
        assert error is exc.value
        assert type is int
        return "an integer is required"

    assert transform_error(exc.value, format_exception=my_format) == [
        "an integer is required @ $"
    ]


def test_primitive_error_pickling(c: Converter) -> None:
    """Primitive errors retain their target type after pickling."""
    with raises(ValueError) as exc:
        c.structure("x", int)

    error = pickle.loads(pickle.dumps(exc.value))  # noqa: S301
    assert transform_error(error) == ["invalid value for type, expected int @ $"]


@mark.parametrize("cl", [int, float])
def test_primitive_errors_without_detailed_validation(converter_cls, cl: type) -> None:
    """Disabling detailed validation leaves primitive errors without notes."""
    c = converter_cls(detailed_validation=False)
    with raises(ValueError) as exc:
        c.structure("x", cl)

    assert not hasattr(exc.value, "__notes__")
    assert transform_error(exc.value) == ["invalid value @ $"]


@mark.parametrize("group_cls", [ClassValidationError, IterableValidationError])
@mark.parametrize("with_type_note", [True, False])
def test_group_errors_without_context(group_cls, with_type_note: bool) -> None:
    """Errors without attribute or index notes use type notes when present."""
    exc = ValueError("Test")
    exc.__notes__ = ["A string note"]
    if with_type_note:
        exc.__notes__.append(TypeValidationNote("Structuring int", int))
    group = group_cls("Test", [exc], int)

    expected = (
        "invalid value for type, expected int" if with_type_note else "invalid value"
    )
    assert transform_error(group) == [f"{expected} @ $"]


def test_recursive_structure_type_note(c: Converter) -> None:
    """Recursive structuring keeps only the innermost target type note."""
    c.register_structure_hook(float, lambda v, _: c.structure(v, int))

    with raises(ValueError) as exc:
        c.structure("x", float)

    assert len(exc.value.__notes__) == 1
    note = exc.value.__notes__[0]
    assert isinstance(note, TypeValidationNote)
    assert note == f"Structuring {int}"
    assert note.type is int
    assert transform_error(exc.value) == ["invalid value for type, expected int @ $"]


def test_structure_preserves_existing_notes(c: Converter) -> None:
    """An exception with existing notes is re-raised unchanged."""
    error = ValueError("Test")
    error.__notes__ = notes = ["A string note"]

    def hook(v, _):
        raise error

    c.register_structure_hook(int, hook)
    with raises(ValueError) as exc:
        c.structure("x", int)

    assert exc.value is error
    assert error.__notes__ is notes
    assert transform_error(error) == ["invalid value @ $"]


@mark.parametrize("exc_cls", [KeyboardInterrupt, SystemExit])
def test_structure_base_exception_without_notes(c: Converter, exc_cls) -> None:
    """Exceptions outside Exception are re-raised without notes."""
    error = exc_cls()

    def hook(v, _):
        raise error

    c.register_structure_hook(int, hook)
    with raises(exc_cls) as exc:
        c.structure("x", int)

    assert exc.value is error
    assert not hasattr(error, "__notes__")


def test_attribute_errors(c: Converter) -> None:
    @define
    class C:
        a: int
        b: int = 0

    try:
        c.structure({}, C)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $.b"]

    @define
    class D:
        c: C

    try:
        c.structure({}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c"]

    try:
        c.structure({"c": {}}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c.a"]

    try:
        c.structure({"c": 1}, D)
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected C @ $.c"]

    try:
        c.structure({"c": {"a": "str"}}, D)
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $.c.a"]

    @define
    class E:
        a: Optional[int]

    with raises(Exception) as exc:
        c.structure({"a": "str"}, E)

    # Complicated due to various Python versions.
    tn = (
        Optional[int].__name__
        if hasattr(Optional[int], "__name__")
        else repr(Optional[int])
    )
    assert transform_error(exc.value) == [
        f"invalid value for type, expected {tn} @ $.a"
    ]


def test_class_errors(c: Converter) -> None:
    """Errors not directly related to attributes are parsed correctly."""

    @define
    class C:
        a: int
        b: int = 0

    c.register_structure_hook(
        C, make_dict_structure_fn(C, c, _cattrs_forbid_extra_keys=True)
    )

    try:
        c.structure({"d": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.a",
            "extra fields found (d) @ $",
        ]


def test_extra_keys_are_sorted(c: Converter) -> None:
    """Extra keys are reported in a stable order.

    `ForbiddenExtraKeysError.extra_fields` is a set, so the message used to
    depend on the iteration order of that set, which differs between processes.
    """

    @define
    class C:
        a: int

    c.register_structure_hook(
        C, make_dict_structure_fn(C, c, _cattrs_forbid_extra_keys=True)
    )

    with raises(Exception) as exc_info:
        c.structure({"a": 1, "e": 2, "c": 3, "b": 4, "d": 5}, C)

    assert transform_error(exc_info.value) == ["extra fields found (b, c, d, e) @ $"]


def test_untyped_class_errors(c: Converter) -> None:
    """Errors on untyped attrs classes transform correctly."""

    @define
    class C:
        a = field()

    def struct_hook(v, __):
        if v == 0:
            raise ValueError()
        raise TypeError("wrong type")

    c.register_structure_hook_func(lambda t: t is None, struct_hook)

    with raises(Exception) as exc_info:
        c.structure({"a": 0}, C)

    assert transform_error(exc_info.value) == ["invalid value @ $.a"]

    with raises(Exception) as exc_info:
        c.structure({"a": 1}, C)

    assert transform_error(exc_info.value) == ["invalid type (wrong type) @ $.a"]


def test_sequence_errors(c: Converter) -> None:
    try:
        c.structure(["str", 1, "str"], List[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $[0]",
            "invalid value for type, expected int @ $[2]",
        ]

    try:
        c.structure(1, List[int])
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected List @ $"]

    try:
        c.structure(["str", 1, "str"], Tuple[int, ...])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $[0]",
            "invalid value for type, expected int @ $[2]",
        ]

    try:
        c.structure(["str", 1, "str"], Sequence[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $[0]",
            "invalid value for type, expected int @ $[2]",
        ]

    try:
        c.structure(["str", 1, "str"], MutableSequence[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $[0]",
            "invalid value for type, expected int @ $[2]",
        ]

    @define
    class C:
        a: List[int]
        b: List[List[int]] = Factory(list)

    try:
        c.structure({"a": ["str", 1, "str"]}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $.a[0]",
            "invalid value for type, expected int @ $.a[2]",
        ]

    try:
        c.structure({"a": [], "b": [[], ["str", 1, "str"]]}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $.b[1][0]",
            "invalid value for type, expected int @ $.b[1][2]",
        ]

    # IterableValidationErrors with subexceptions without notes
    exc = IterableValidationError("Test", [TypeError("Test")], list[str])

    assert transform_error(exc) == ["invalid type (Test) @ $"]


def test_mapping_errors(c: Converter) -> None:
    try:
        c.structure({"a": 1, "b": "str"}, Dict[str, int])
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $['b']"]

    @define
    class C:
        a: Dict[str, int]

    try:
        c.structure({"a": {"a": "str", "b": 1, "c": "str"}}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $.a['a']",
            "invalid value for type, expected int @ $.a['c']",
        ]

    try:
        c.structure({"a": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == ["expected a mapping @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, Mapping[str, int])
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $['b']"]

    try:
        c.structure({"a": 1, "b": "str"}, MutableMapping[str, int])
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $['b']"]

    try:
        c.structure({"a": 1, 2: "str"}, MutableMapping[int, int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $['a']",
            "invalid value for type, expected int @ $[2]",
        ]


def test_custom_error_fn(c: Converter) -> None:
    def my_format(exc, type):
        if isinstance(exc, KeyError):
            return "no key"
        return format_exception(exc, type)

    @define
    class C:
        a: int
        b: int = 1

    try:
        c.structure({"b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc, format_exception=my_format) == [
            "no key @ $.a",
            "invalid value for type, expected int @ $.b",
        ]


def test_custom_error_fn_nested(c: Converter) -> None:
    def my_format(exc, type):
        if isinstance(exc, TypeError):
            return "Must be correct type"
        return format_exception(exc, type)

    @define
    class C:
        a: Dict[str, int]

    try:
        c.structure({"a": {"a": "str", "b": 1, "c": None}}, C)
    except Exception as exc:
        assert transform_error(exc, format_exception=my_format) == [
            "invalid value for type, expected int @ $.a['a']",
            "Must be correct type @ $.a['c']",
        ]


def test_typeddict_attribute_errors(c: Converter) -> None:
    """TypedDict errors are correctly generated."""

    class C(TypedDict):
        a: int
        b: int

    try:
        c.structure({}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.a",
            "required field missing @ $.b",
        ]

    try:
        c.structure({"b": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected int @ $.b"]

    class D(TypedDict):
        c: C

    try:
        c.structure({}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c"]

    try:
        c.structure({"c": {}}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.c.a",
            "required field missing @ $.c.b",
        ]

    try:
        c.structure({"c": 1}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid type (expected a mapping, not int) @ $.c"
        ]

    try:
        c.structure({"c": {"a": "str"}}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int @ $.c.a",
            "required field missing @ $.c.b",
        ]

    class E(TypedDict):
        a: Optional[int]

    with raises(Exception) as exc:
        c.structure({"a": "str"}, E)

    # Complicated due to various Python versions.
    tn = (
        Optional[int].__name__
        if hasattr(Optional[int], "__name__")
        else repr(Optional[int])
    )
    assert transform_error(exc.value) == [
        f"invalid value for type, expected {tn} @ $.a"
    ]


def test_other_errors():
    """Errors without explicit support transform predictably."""
    assert format_exception(IndexError("Test"), List[int]) == "unknown error (Test)"
    assert transform_error(TypeError("'int' object is not iterable")) == [
        "invalid value for type, expected an iterable @ $"
    ]
