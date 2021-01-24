from cattr.converters import GenConverter
import attr


def test_inheritance():
    @attr.s(auto_attribs=True)
    class A:
        i: int

    @attr.s(auto_attribs=True)
    class B(A):
        j: int

    converter = GenConverter()

    # succeeds
    assert A(1) == converter.structure(dict(i=1), A)

    # fails
    assert B(1, 2) == converter.structure(dict(i=1, j=2), B)
