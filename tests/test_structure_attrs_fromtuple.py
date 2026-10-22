"""Structuring attrs classes and dataclasses from tuples."""

from dataclasses import dataclass
from dataclasses import field as dc_field

import pytest
from attrs import define, field

from cattrs import UnstructureStrategy


@pytest.fixture
def tuple_converter(converter_cls):
    return converter_cls(unstruct_strat=UnstructureStrategy.AS_TUPLE)


@pytest.mark.parametrize("class_decorator", [define, dataclass])
def test_kw_only(class_decorator, tuple_converter):
    """Class-wide keyword-only fields can be structured directly and dispatched."""

    @class_decorator(kw_only=True)
    class C:
        a: int
        b: int

    expected = C(a=1, b=2)
    assert tuple_converter.structure_attrs_fromtuple(("1", "2"), C) == expected
    assert tuple_converter.structure(("1", "2"), C) == expected
    assert (
        tuple_converter.structure(tuple_converter.unstructure(expected), C) == expected
    )


@pytest.mark.parametrize(
    "class_decorator, field_factory", [(define, field), (dataclass, dc_field)]
)
def test_kw_only_inheritance(class_decorator, field_factory, tuple_converter):
    """Inherited and interleaved keyword-only fields retain their tuple positions."""

    @class_decorator(kw_only=True)
    class Parent:
        a: int

    @class_decorator
    class Child(Parent):
        b: int
        c: int = field_factory(kw_only=True)
        d: int

    expected = Child(2, 4, a=1, c=3)
    assert tuple_converter.unstructure(expected) == (1, 2, 3, 4)
    assert tuple_converter.structure(("1", "2", "3", "4"), Child) == expected


def test_kw_only_aliases(tuple_converter):
    """Use constructor aliases, including attrs' default private-field aliases."""

    @define
    class C:
        positional: int = field(alias="arg")
        _private: int = field(kw_only=True)
        named: int = field(kw_only=True, alias="renamed")
        _explicit: int = field(kw_only=True, alias="_explicit")

    expected = C(1, private=2, renamed=3, _explicit=4)
    assert tuple_converter.structure(("1", "2", "3", "4"), C) == expected
    assert (
        tuple_converter.structure(tuple_converter.unstructure(expected), C) == expected
    )


@pytest.mark.parametrize(
    "class_decorator, field_factory", [(define, field), (dataclass, dc_field)]
)
@pytest.mark.parametrize("values", [(), ("1",), ("1", "2"), ("1", "2", "3")])
def test_defaults(class_decorator, field_factory, values, tuple_converter):
    """A short tuple still leaves omitted constructor arguments at their defaults."""

    @class_decorator
    class C:
        a: int = 1
        b: int = field_factory(kw_only=True, default=2)
        c: int = 3

    assert tuple_converter.structure(values, C) == C()


@pytest.mark.parametrize("prefer_attrib_converters", [False, True])
def test_kw_only_attrib_converters(converter_cls, prefer_attrib_converters):
    """Keyword-only fields retain structuring-hook and attrs-converter precedence."""
    converter = converter_cls(
        unstruct_strat=UnstructureStrategy.AS_TUPLE,
        prefer_attrib_converters=prefer_attrib_converters,
    )
    converter.register_structure_hook(int, lambda value, _: int(value) * 2)

    @define
    class C:
        a: int = field(kw_only=True, converter=lambda value: int(value) + 1)

    assert converter.structure(("3",), C).a == (4 if prefer_attrib_converters else 7)
