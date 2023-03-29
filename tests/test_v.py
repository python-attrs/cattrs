"""Tests for the cattrs.v framework."""
from typing import Dict, List, MutableMapping, MutableSequence, Sequence, Tuple

from attrs import Factory, define
from pytest import fixture

from cattrs import Converter, transform_error
from cattrs._compat import Mapping
from cattrs.gen import make_dict_structure_fn
from cattrs.v import format_exception


@fixture
def c() -> Converter:
    """We need only converters with detailed_validation=True."""
    return Converter()


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
        assert transform_error(exc) == [
            "invalid value for type, expected an iterable @ $"
        ]

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
