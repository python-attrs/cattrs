"""Tests for enums."""

from enum import Enum

from attrs import define
from hypothesis import given
from hypothesis.strategies import data, sampled_from
from pytest import raises

from cattrs import BaseConverter
from cattrs._compat import Literal
from cattrs.errors import CattrsError

from .untyped import enums_of_primitives


@given(data(), enums_of_primitives())
def test_structuring_enums(data, enum):
    """Test structuring enums by their values."""
    converter = BaseConverter()
    val = data.draw(sampled_from(list(enum)))

    assert converter.structure(val.value, enum) == val


@given(enums_of_primitives())
def test_enum_failure(enum):
    """Structuring literals with enums fails properly."""
    converter = BaseConverter()
    type = Literal[next(iter(enum))]

    with raises(CattrsError) as exc_info:
        converter.structure("", type)

    assert exc_info.value.args[0] == f" not in literal {type!r}"


class SimpleEnum(Enum):
    A = 0
    B = 1
    C = 2


class SimpleEnumWithTypeHint(Enum):
    _value_: str
    D = "D"
    E = "E"
    F = "F"


class ComplexEnum(Enum):
    _value_: tuple[SimpleEnum, SimpleEnumWithTypeHint]
    AD = (SimpleEnum.A, SimpleEnumWithTypeHint.D)
    AE = (SimpleEnum.A, SimpleEnumWithTypeHint.E)
    BE = (SimpleEnum.B, SimpleEnumWithTypeHint.E)
    BF = (SimpleEnum.B, SimpleEnumWithTypeHint.F)
    CE = (SimpleEnum.C, SimpleEnumWithTypeHint.E)


def test_unstructure_complex_enum() -> None:
    converter = BaseConverter()
    assert converter.unstructure(SimpleEnum.A) == 0
    assert converter.unstructure(SimpleEnumWithTypeHint.F) == "F"
    assert converter.unstructure(ComplexEnum.AE) == (0, "E")


def test_structure_complex_enum() -> None:
    converter = BaseConverter()
    assert converter.structure(0, SimpleEnum) == SimpleEnum.A
    assert converter.structure("E", SimpleEnumWithTypeHint) == SimpleEnumWithTypeHint.E
    assert converter.structure((0, "D"), ComplexEnum) == ComplexEnum.AD


class EnumValuedEnum(Enum):
    """Enum whose members have other Enum instances as values (no type annotation)."""

    X = SimpleEnum.A
    Y = SimpleEnum.B


class TupleValuedEnum(Enum):
    """Enum whose members have tuples with Enum instances (no type annotation)."""

    X = (SimpleEnum.A, 1)


@define
class AnAttrsClass:
    a: int


class AttrsValuedEnum(Enum):
    """Enum whose members have attrs instances as values (no type annotation)."""

    X = AnAttrsClass(1)


def test_unstructure_simple_enum_uses_value_directly() -> None:
    """Simple enum values do not recurse through the converter."""
    converter = BaseConverter()
    converter.register_unstructure_hook(int, lambda _: "overridden")

    assert converter.unstructure(SimpleEnum.A) == 0


def test_unstructure_enum_with_enum_values() -> None:
    """Enum members whose values are themselves Enums are unstructured recursively.

    Regression test for https://github.com/python-attrs/cattrs/issues/679.
    """
    converter = BaseConverter()
    assert converter.unstructure(EnumValuedEnum.X) == 0
    assert converter.unstructure(EnumValuedEnum.Y) == 1


def test_unstructure_enum_with_tuple_values() -> None:
    """Enum member tuples containing Enums are unstructured recursively."""
    converter = BaseConverter()
    assert converter.unstructure(TupleValuedEnum.X) == (0, 1)


def test_unstructure_enum_with_attrs_values() -> None:
    """Enum members whose values are attrs classes are unstructured recursively."""
    converter = BaseConverter()
    assert converter.unstructure(AttrsValuedEnum.X) == {"a": 1}
