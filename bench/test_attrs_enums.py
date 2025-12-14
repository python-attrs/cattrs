from enum import Enum, IntEnum

import pytest
from attrs import define

from cattr import BaseConverter, Converter


class SimpleEnum(Enum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class SimpleIntEnum(IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


@define
class EnumContainer:
    simple_enum: SimpleEnum
    simple_int_enum: SimpleIntEnum


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


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_attrs_enum_container(benchmark, converter_cls):
    """Benchmark unstructuring an attrs class containing enums."""
    c = converter_cls()
    instance = EnumContainer(simple_enum=SimpleEnum.SECOND, simple_int_enum=SimpleIntEnum.TWO)
    benchmark(c.unstructure, instance)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_attrs_enum_container(benchmark, converter_cls):
    """Benchmark structuring an attrs class containing enums."""
    c = converter_cls()
    data = {"simple_enum": "second", "simple_int_enum": 2}
    benchmark(c.structure, data, EnumContainer)
