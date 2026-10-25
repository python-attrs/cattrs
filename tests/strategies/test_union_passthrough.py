"""Tests for the native union passthrough strategy.

Note that a significant amount of test coverage for this is in the
preconf tests.
"""

from copy import deepcopy
from datetime import datetime
from typing import List, Literal, Optional, Union

import pytest
from attrs import define

from cattrs import (
    BaseConverter,
    ClassValidationError,
    Converter,
    ForbiddenExtraKeysError,
)
from cattrs.preconf.json import make_converter
from cattrs.strategies import configure_union_passthrough


def test_only_primitives(converter: BaseConverter) -> None:
    """A native union with only primitives works."""
    union = Union[int, str, None]
    configure_union_passthrough(union, converter)

    assert converter.unstructure(1, union) == 1
    assert converter.structure(1, union) == 1
    assert converter.unstructure("1", union) == "1"
    assert converter.structure("1", union) == "1"
    assert converter.unstructure(None, union) is None
    assert converter.structure(None, union) is None

    with pytest.raises(TypeError):
        converter.structure((), union)


def test_literals(converter: BaseConverter) -> None:
    """A union with primitives and literals works."""

    union = Union[int, str, None]
    exact_type = Union[int, Literal["test"], None]
    configure_union_passthrough(union, converter)

    assert converter.unstructure(1, exact_type) == 1
    assert converter.structure(1, exact_type) == 1
    assert converter.unstructure("test", exact_type) == "test"
    assert converter.structure("test", exact_type) == "test"
    assert converter.unstructure(None, exact_type) is None
    assert converter.structure(None, exact_type) is None

    with pytest.raises(TypeError):
        converter.structure((), exact_type)
    with pytest.raises(TypeError):
        converter.structure("t", exact_type)


def test_skip_optionals() -> None:
    """
    The strategy skips Optionals, since those are more efficiently
    handled by default.
    """
    c = BaseConverter()

    configure_union_passthrough(Union[int, str, None], c)

    h = c.get_structure_hook(Optional[int])
    assert h.__name__ != "structure_native_union"


def test_spillover(converter: BaseConverter) -> None:
    """Types not covered by the native union are correctly handled."""
    union = Union[int, str, None]
    exact_type = Union[int, List[str], None]

    configure_union_passthrough(union, converter)

    assert converter.unstructure(1, exact_type) == 1
    assert converter.structure(1, exact_type) == 1

    assert converter.unstructure(["a", "b"], exact_type) == ["a", "b"]
    assert converter.structure(["a", "b"], exact_type) == ["a", "b"]

    with pytest.raises(TypeError):
        converter.structure((), union)


@pytest.mark.parametrize("copy_method", ["copy", "deepcopy"])
def test_copy_spillover_hooks(converter: BaseConverter, copy_method: str) -> None:
    """A copy uses its own spillover hooks, including after a union was cached."""

    @define
    class A:
        value: str

    configure_union_passthrough(Union[int, str, None], converter)
    converter.register_structure_hook(A, lambda value, _: A(f"original:{value}"))
    union = Union[int, A, None]

    assert converter.structure("value", union) == A("original:value")
    copied = converter.copy() if copy_method == "copy" else deepcopy(converter)
    assert copied.structure("value", union) == A("original:value")

    copied.register_structure_hook(A, lambda value, _: A(f"copy:{value}"))

    assert copied.structure("value", union) == A("copy:value")
    assert converter.structure("value", union) == A("original:value")
    assert copied.structure(1, union) == 1
    assert copied.structure(None, union) is None


def test_copy_spillover_forbid_extra_keys(genconverter: Converter) -> None:
    """Configuration overridden on a copy also applies to union spillover."""

    @define
    class A:
        value: int

    configure_union_passthrough(Union[int, str], genconverter)
    union = Union[int, A]
    payload = {"value": 1, "extra": 2}
    assert genconverter.structure(payload, union) == A(1)

    copied = genconverter.copy(forbid_extra_keys=True)
    assert copied.structure({"value": 1}, union) == A(1)

    with pytest.raises(
        ClassValidationError if copied.detailed_validation else ForbiddenExtraKeysError
    ):
        copied.structure(payload, union)

    assert genconverter.structure(payload, union) == A(1)
    assert copied.structure(1, union) == 1


def test_copy_json_spillover() -> None:
    """A copied JSON converter uses its datetime hook when loading a union."""
    converter = make_converter()
    union = Union[int, datetime, None]
    expected = datetime(2000, 1, 2)
    assert converter.loads('"2000-01-02T00:00:00"', union) == expected

    copied = converter.copy()
    copied.register_structure_hook(
        datetime, lambda value, _: datetime.fromisoformat(value.replace("/", "-"))
    )

    assert copied.loads('"2000/01/02"', union) == expected
    assert converter.loads('"2000-01-02T00:00:00"', union) == expected
    assert copied.loads("1", union) == 1
    assert copied.loads("null", union) is None


def test_multiple_spillover(converter: BaseConverter) -> None:
    """Types not covered by the native union are correctly handled."""
    union = Union[int, str, None]

    @define
    class A:
        a: int

    @define
    class B:
        b: int

    # A | B will be handled by the default disambiguator.
    exact_type = Union[int, List[str], A, B, None]

    configure_union_passthrough(union, converter)

    assert converter.unstructure(1, exact_type) == 1
    assert converter.structure(1, exact_type) == 1

    assert converter.unstructure(["a", "b"], exact_type) == ["a", "b"]
    assert converter.structure(["a", "b"], List[str]) == ["a", "b"]
    assert converter.unstructure(A(1), exact_type) == {"a": 1}
    assert converter.structure({"a": 1}, A) == A(1)
    assert converter.unstructure(B(1), exact_type) == {"b": 1}
    assert converter.structure({"b": 1}, B) == B(1)

    with pytest.raises(TypeError):
        converter.structure((), union)


def test_int_is_float(converter: BaseConverter) -> None:
    """By default, ints can also be accepted when floats are.

    When the strategy gets initialized with both ints and floats,
    unions that only contain floats also accept ints by default.
    """

    configure_union_passthrough(Union[int, float, str, None], converter)

    assert converter.structure(1, Union[float, str, None]) == 1
    assert isinstance(converter.structure(1, Union[float, str, None]), int)


def test_int_is_not_float(converter: BaseConverter) -> None:
    """Ints can be configured to be separate."""

    @define
    class A:
        a: int

    configure_union_passthrough(
        Union[int, float], converter, accept_ints_as_floats=False
    )

    with pytest.raises(
        ClassValidationError
        if isinstance(converter, Converter) and converter.detailed_validation
        else TypeError
    ):
        converter.structure(1, Union[float, A])
