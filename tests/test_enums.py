"""Tests for enums."""

from attrs import NOTHING
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


def test_nothing_from_attrs():
    """Test that `NOTHING` from attrs does not unstructure to `1` (int), but remains `NOTHING`."""
    converter = BaseConverter()

    assert (
        converter.unstructure(NOTHING) != 1
    ), "NOTHING should not unstructure to 1 (int)."
    assert not isinstance(converter.unstructure(NOTHING), int)
    assert not converter.unstructure(
        NOTHING
    )  # bool(NOTHING) should be False although `bool(1)` is True
    assert converter.unstructure(NOTHING) is NOTHING
