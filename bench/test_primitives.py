import pytest

from cattr import BaseConverter, Converter


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_int(benchmark, converter_cls):
    c = converter_cls()

    benchmark(c.unstructure, 5)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_float(benchmark, converter_cls):
    c = converter_cls()

    benchmark(c.unstructure, 15.0)
