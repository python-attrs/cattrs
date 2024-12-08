"""Tests for the list-from-dict strategy."""

from dataclasses import dataclass
from typing import TypedDict

import pytest
from attrs import define, fields

from cattrs import BaseConverter
from cattrs.strategies import configure_list_from_dict


@define
class AttrsA:
    a: int
    b: str


@dataclass
class DataclassA:
    a: int
    b: str


class TypedDictA(TypedDict):
    a: int
    b: str


@pytest.mark.parametrize("cls", [AttrsA, DataclassA, TypedDictA])
def test_simple_roundtrip(
    cls: type[AttrsA] | type[DataclassA], converter: BaseConverter
):
    hook, hook2 = configure_list_from_dict(list[cls], "a", converter)

    structured = [cls(a=1, b="2"), cls(a=3, b="4")]
    unstructured = hook2(structured)
    assert unstructured == {1: {"b": "2"}, 3: {"b": "4"}}

    assert hook(unstructured) == structured


def test_simple_roundtrip_attrs(converter: BaseConverter):
    hook, hook2 = configure_list_from_dict(list[AttrsA], fields(AttrsA).a, converter)

    structured = [AttrsA(a=1, b="2"), AttrsA(a=3, b="4")]
    unstructured = hook2(structured)
    assert unstructured == {1: {"b": "2"}, 3: {"b": "4"}}

    assert hook(unstructured) == structured
