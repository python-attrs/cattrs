"""Tests for the list-from-dict strategy."""

from attrs import define

from cattrs import BaseConverter
from cattrs.strategies import configure_list_from_dict


@define
class A:
    a: int
    b: str


def test_simple_roundtrip(converter: BaseConverter):
    hook, hook2 = configure_list_from_dict(list[A], "a", converter)

    structured = [A(1, "2"), A(3, "4")]
    unstructured = hook2(structured)
    assert unstructured == {1: {"b": "2"}, 3: {"b": "4"}}

    assert hook(unstructured) == structured
