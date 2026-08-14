"""Tests for enums."""

from enum import Enum

import attrs
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


def test_unstructure_enum_misuse_raises_clear_error() -> None:
    """Regression test for #601.

    Unstructuring a value that isn't actually an instance of the expected
    enum (e.g. because the enum's raw value was assigned directly to an
    attribute typed as the enum, bypassing any validation) must raise a
    clear, actionable ``TypeError`` instead of an opaque ``AttributeError``
    like ``'str' object has no attribute 'value'``.
    """
    converter = BaseConverter()

    with raises(TypeError) as exc_info:
        converter.unstructure("A", unstructure_as=SimpleEnum)

    msg = str(exc_info.value)
    assert "SimpleEnum" in msg
    assert "'A'" in msg


def test_unstructure_typed_enum_misuse_raises_clear_error() -> None:
    """Regression test for #601, typed-enum branch (has `_value_`)."""
    converter = BaseConverter()

    with raises(TypeError) as exc_info:
        converter.unstructure("D", unstructure_as=SimpleEnumWithTypeHint)

    msg = str(exc_info.value)
    assert "SimpleEnumWithTypeHint" in msg
    assert "'D'" in msg


def test_unstructure_attrs_class_with_misused_enum_field() -> None:
    """End-to-end regression test for #601, matching the original report.

    Assigning a plain string default (instead of an actual enum member) to
    an attrs attribute typed as an ``Enum`` used to blow up with an
    unhelpful ``AttributeError`` deep inside generated code.
    """

    @attrs.define
    class Site:
        flavor: SimpleEnumWithTypeHint = "D"  # intentionally not an enum member

    converter = BaseConverter()

    with raises(TypeError) as exc_info:
        converter.unstructure(Site())

    msg = str(exc_info.value)
    assert "SimpleEnumWithTypeHint" in msg
    assert "'D'" in msg
