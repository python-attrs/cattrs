import pytest

from cattrs import BaseConverter, Converter

HETERO_TUPLE = tuple[int, str, float, int, str, float]
HETERO_RAW = [1.0, 2, "3", 4.0, 5, "6"]
HETERO_VALUE = (1, "2", 3.0, 4, "5", 6.0)
HOMO_TUPLE = tuple[int, ...]
HOMO_RAW = ["1", 2, 3.0, 4, 5.0, "6"]


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize("detailed_validation", [True, False])
def test_structure_hetero_tuple(benchmark, converter_cls, detailed_validation):
    """Benchmark steady-state heterogeneous tuple structuring."""
    c = converter_cls(detailed_validation=detailed_validation)

    benchmark(c.structure, HETERO_RAW, HETERO_TUPLE)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_unstructure_hetero_tuple(benchmark, converter_cls):
    """Benchmark heterogeneous tuple unstructuring."""
    c = converter_cls()

    benchmark(c.unstructure, HETERO_VALUE, HETERO_TUPLE)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
@pytest.mark.parametrize("detailed_validation", [True, False])
def test_structure_homo_tuple(benchmark, converter_cls, detailed_validation):
    """Benchmark homogeneous tuple structuring."""
    c = converter_cls(detailed_validation=detailed_validation)

    benchmark(c.structure, HOMO_RAW, HOMO_TUPLE)
