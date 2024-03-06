"""Tests for NewTypes."""

from typing import NewType

import pytest

from cattrs import BaseConverter, Converter

PositiveIntNewType = NewType("PositiveIntNewType", int)
BigPositiveIntNewType = NewType("BigPositiveIntNewType", PositiveIntNewType)


def test_newtype_structure_hooks(converter: BaseConverter):
    """NewTypes should work with `register_structure_hook`."""

    assert converter.structure("0", int) == 0
    assert converter.structure("0", PositiveIntNewType) == 0
    assert converter.structure("0", BigPositiveIntNewType) == 0

    converter.register_structure_hook(
        PositiveIntNewType, lambda v, _: int(v) if int(v) > 0 else 1 / 0
    )

    with pytest.raises(ZeroDivisionError):
        converter.structure("0", PositiveIntNewType)

    assert converter.structure("1", PositiveIntNewType) == 1

    with pytest.raises(ZeroDivisionError):
        converter.structure("0", BigPositiveIntNewType)

    converter.register_structure_hook(
        BigPositiveIntNewType, lambda v, _: int(v) if int(v) > 50 else 1 / 0
    )

    with pytest.raises(ZeroDivisionError):
        converter.structure("1", BigPositiveIntNewType)

    assert converter.structure("1", PositiveIntNewType) == 1
    assert converter.structure("51", BigPositiveIntNewType) == 51


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
