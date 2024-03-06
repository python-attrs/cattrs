"""Tests for the native union passthrough strategy.

Note that a significant amount of test coverage for this is in the
preconf tests.
"""

from typing import List, Optional, Union

import pytest
from attrs import define

from cattrs import BaseConverter
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
    from typing import Literal

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
