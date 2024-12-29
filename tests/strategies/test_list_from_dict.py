"""Tests for the list-from-dict strategy."""

from dataclasses import dataclass
from typing import TypedDict, Union

import pytest
from attrs import define, fields

from cattrs import BaseConverter, transform_error
from cattrs.converters import Converter
from cattrs.errors import IterableValidationError
from cattrs.gen import make_dict_structure_fn
from cattrs.strategies import configure_list_from_dict


@define
class AttrsA:
    a: int
    b: int


@dataclass
class DataclassA:
    a: int
    b: int


class TypedDictA(TypedDict):
    a: int
    b: int


@pytest.mark.parametrize("cls", [AttrsA, DataclassA, TypedDictA])
def test_simple_roundtrip(
    cls: Union[type[AttrsA], type[DataclassA]], converter: BaseConverter
):
    hook, hook2 = configure_list_from_dict(list[cls], "a", converter)

    structured = [cls(a=1, b=2), cls(a=3, b=4)]
    unstructured = hook2(structured)
    assert unstructured == {1: {"b": 2}, 3: {"b": 4}}

    assert hook(unstructured) == structured


def test_simple_roundtrip_attrs(converter: BaseConverter):
    hook, hook2 = configure_list_from_dict(list[AttrsA], fields(AttrsA).a, converter)

    structured = [AttrsA(a=1, b=2), AttrsA(a=3, b=4)]
    unstructured = hook2(structured)
    assert unstructured == {1: {"b": 2}, 3: {"b": 4}}

    assert hook(unstructured) == structured


def test_validation_errors():
    """
    With detailed validation, validation errors should be adjusted for the
    extracted keys.
    """
    conv = Converter(detailed_validation=True)
    hook, _ = configure_list_from_dict(list[AttrsA], "a", conv)

    # Key failure
    with pytest.raises(IterableValidationError) as exc:
        hook({"a": {"b": "1"}})

    assert transform_error(exc.value) == [
        "invalid value for type, expected int @ $['a']"
    ]

    # Value failure
    with pytest.raises(IterableValidationError) as exc:
        hook({1: {"b": "a"}})

    assert transform_error(exc.value) == [
        "invalid value for type, expected int @ $[1].b"
    ]

    conv.register_structure_hook(
        AttrsA, make_dict_structure_fn(AttrsA, conv, _cattrs_forbid_extra_keys=True)
    )
    hook, _ = configure_list_from_dict(list[AttrsA], "a", conv)

    # Value failure, not attribute related
    with pytest.raises(IterableValidationError) as exc:
        hook({1: {"b": 1, "c": 2}})

    assert transform_error(exc.value) == ["extra fields found (c) @ $[1]"]
