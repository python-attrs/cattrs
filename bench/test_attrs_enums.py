from enum import Enum, IntEnum

import pytest

from cattrs import BaseConverter, Converter


class SimpleEnum(Enum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class SimpleIntEnum(IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_simple_enum(benchmark, converter_cls):
    """Benchmark unstructuring a simple enum."""
    c = converter_cls()
    benchmark(c.unstructure, SimpleEnum.FIRST)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_simple_enum(benchmark, converter_cls):
    """Benchmark structuring a simple enum."""
    c = converter_cls()
    benchmark(c.structure, "first", SimpleEnum)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_simple_int_enum(benchmark, converter_cls):
    """Benchmark unstructuring a simple IntEnum."""
    c = converter_cls()
    benchmark(c.unstructure, SimpleIntEnum.ONE)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_simple_int_enum(benchmark, converter_cls):
    """Benchmark structuring a simple IntEnum."""
    c = converter_cls()
    benchmark(c.structure, 1, SimpleIntEnum)
