"""Tests for enums."""

from enum import Enum

from hypothesis import given
from hypothesis.strategies import data, sampled_from
from pytest import raises

from cattrs import BaseConverter
from cattrs._compat import Literal

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

    with raises(Exception) as exc_info:
        converter.structure("", type)

    assert exc_info.value.args[0] == f" not in literal {type!r}"


class E(Enum):
    _value_: int
    A = 0


class EE(Enum):
    _value_: tuple[E, int]
    A1 = (E.A, 1)


def test_unstructure_complex_enum() -> None:
    converter = BaseConverter()
    assert converter.unstructure(E.A) == 0
    assert converter.unstructure(EE.A1) == (0, 1)


def test_structure_complex_enum() -> None:
    converter = BaseConverter()
    assert converter.structure(0, E) == E.A
    assert converter.structure((0, 1), EE) == EE.A1
