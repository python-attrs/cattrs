from typing import Literal, Optional, Union

import pytest

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

    h = c._structure_func.dispatch(Optional[int])
    assert h.__name__ != "structure_native_union"
