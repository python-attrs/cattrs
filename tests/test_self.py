"""Tests for `typing.Self`."""

from dataclasses import dataclass
from typing import NamedTuple, Optional, TypedDict

from attrs import define
from typing_extensions import Self

from cattrs import Converter
from cattrs.cols import (
    namedtuple_dict_structure_factory,
    namedtuple_dict_unstructure_factory,
)


@define
class WithSelf:
    myself: Optional[Self]
    myself_with_default: Optional[Self] = None


@define
class WithSelfSubclass(WithSelf):
    pass


@dataclass
class WithSelfDataclass:
    myself: Optional[Self]


@dataclass
class WithSelfDataclassSubclass(WithSelfDataclass):
    pass


@define
class WithListOfSelf:
    myself: Optional[Self]
    selves: list[WithSelf]


class WithSelfTypedDict(TypedDict):
    field: int
    myself: Optional[Self]


class WithSelfNamedTuple(NamedTuple):
    myself: Optional[Self]


def test_self_roundtrip(genconverter):
    """A simple roundtrip works."""
    initial = WithSelf(WithSelf(None, WithSelf(None)))
    raw = genconverter.unstructure(initial)

    assert raw == {
        "myself": {
            "myself": None,
            "myself_with_default": {"myself": None, "myself_with_default": None},
        },
        "myself_with_default": None,
    }

    assert genconverter.structure(raw, WithSelf) == initial


def test_self_roundtrip_dataclass(genconverter):
    """A simple roundtrip works for dataclasses."""
    initial = WithSelfDataclass(WithSelfDataclass(None))
    raw = genconverter.unstructure(initial)

    assert raw == {"myself": {"myself": None}}

    assert genconverter.structure(raw, WithSelfDataclass) == initial


def test_self_roundtrip_typeddict(genconverter):
    """A simple roundtrip works for TypedDicts."""
    genconverter.register_unstructure_hook(int, str)

    initial: WithSelfTypedDict = {"field": 1, "myself": {"field": 2, "myself": None}}
    raw = genconverter.unstructure(initial)

    assert raw == {"field": "1", "myself": {"field": "2", "myself": None}}

    assert genconverter.structure(raw, WithSelfTypedDict) == initial


def test_self_roundtrip_namedtuple(genconverter):
    """A simple roundtrip works for NamedTuples."""
    genconverter.register_unstructure_hook_factory(
        lambda t: t is WithSelfNamedTuple, namedtuple_dict_unstructure_factory
    )
    genconverter.register_structure_hook_factory(
        lambda t: t is WithSelfNamedTuple, namedtuple_dict_structure_factory
    )

    initial = WithSelfNamedTuple(WithSelfNamedTuple(None))
    raw = genconverter.unstructure(initial)

    assert raw == {"myself": {"myself": None}}

    assert genconverter.structure(raw, WithSelfNamedTuple) == initial


def test_subclass_roundtrip(genconverter):
    """A simple roundtrip works for a dataclass subclass."""
    initial = WithSelfSubclass(WithSelfSubclass(None))
    raw = genconverter.unstructure(initial)

    assert raw == {
        "myself": {"myself": None, "myself_with_default": None},
        "myself_with_default": None,
    }

    assert genconverter.structure(raw, WithSelfSubclass) == initial


def test_subclass_roundtrip_dataclass(genconverter):
    """A simple roundtrip works for a dataclass subclass."""
    initial = WithSelfDataclassSubclass(WithSelfDataclassSubclass(None))
    raw = genconverter.unstructure(initial)

    assert raw == {"myself": {"myself": None}}

    assert genconverter.structure(raw, WithSelfDataclassSubclass) == initial


def test_nested_roundtrip(genconverter: Converter):
    """A more complex roundtrip, with several Self classes."""
    initial = WithListOfSelf(WithListOfSelf(None, []), [WithSelf(WithSelf(None))])
    raw = genconverter.unstructure(initial)

    assert raw == {
        "myself": {"myself": None, "selves": []},
        "selves": [
            {
                "myself": {"myself": None, "myself_with_default": None},
                "myself_with_default": None,
            }
        ],
    }

    assert genconverter.structure(raw, WithListOfSelf) == initial
