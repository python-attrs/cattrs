"""Tests for NewTypes."""
from typing import NewType

import pytest

from cattrs import Converter

PositiveIntNewType = NewType("PositiveIntNewType", int)
BigPositiveIntNewType = NewType("BigPositiveIntNewType", PositiveIntNewType)


def test_newtype_structure_hooks(genconverter: Converter):
    """NewTypes should work with `register_structure_hook`."""

    assert genconverter.structure("0", int) == 0
    assert genconverter.structure("0", PositiveIntNewType) == 0
    assert genconverter.structure("0", BigPositiveIntNewType) == 0

    genconverter.register_structure_hook(
        PositiveIntNewType, lambda v, _: int(v) if int(v) > 0 else 1 / 0
    )

    with pytest.raises(ZeroDivisionError):
        genconverter.structure("0", PositiveIntNewType)

    assert genconverter.structure("1", PositiveIntNewType) == 1

    with pytest.raises(ZeroDivisionError):
        genconverter.structure("0", BigPositiveIntNewType)

    genconverter.register_structure_hook(
        BigPositiveIntNewType, lambda v, _: int(v) if int(v) > 50 else 1 / 0
    )

    with pytest.raises(ZeroDivisionError):
        genconverter.structure("1", BigPositiveIntNewType)

    assert genconverter.structure("1", PositiveIntNewType) == 1
    assert genconverter.structure("51", BigPositiveIntNewType) == 51


def test_newtype_unstructure_hooks(genconverter: Converter):
    """NewTypes should work with `register_unstructure_hook`."""

    assert genconverter.unstructure(0, int) == 0
    assert genconverter.unstructure(0, PositiveIntNewType) == 0
    assert genconverter.unstructure(0, BigPositiveIntNewType) == 0

    genconverter.register_unstructure_hook(PositiveIntNewType, oct)

    assert genconverter.unstructure(0, PositiveIntNewType) == "0o0"
    assert genconverter.unstructure(0, BigPositiveIntNewType) == "0o0"

    genconverter.register_unstructure_hook(BigPositiveIntNewType, hex)

    assert genconverter.unstructure(0, PositiveIntNewType) == "0o0"
    assert genconverter.unstructure(0, BigPositiveIntNewType) == "0x0"
