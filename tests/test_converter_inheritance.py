import attr
import pytest

from cattr.converters import Converter, GenConverter


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_inheritance(converter_cls):
    @attr.s(auto_attribs=True)
    class A:
        i: int

    @attr.s(auto_attribs=True)
    class B(A):
        j: int

    converter = converter_cls()

    # succeeds
    assert A(1) == converter.structure(dict(i=1), A)

    # fails
    assert B(1, 2) == converter.structure(dict(i=1, j=2), B)
