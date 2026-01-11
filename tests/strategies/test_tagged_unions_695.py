from __future__ import annotations

from attrs import define

from cattrs import BaseConverter, Converter
from cattrs.strategies import configure_tagged_union

from .test_tagged_unions import A, B


def test_type_alias(converter: BaseConverter):
    """Type aliases to unions also work."""
    type AOrB = A | B

    configure_tagged_union(AOrB, converter)

    assert converter.unstructure(A(1), AOrB) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), AOrB) == {"_type": "B", "a": "1"}

    assert converter.structure({"_type": "A", "a": 1}, AOrB) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, AOrB) == B("1")


@define
class Lit:
    value: float


@define
class Add:
    left: Expr
    right: Expr


type Expr = Add | Lit


def test_recursive_type_alias(genconverter: Converter):
    """Recursive type aliases to unions also work.

    Only tests on the GenConverter since the BaseConverter doesn't support
    stringified annotations.
    """

    configure_tagged_union(Expr, genconverter)

    val = Add(Lit(1.0), Lit(2.0))
    expected = {
        "_type": "Add",
        "left": {"_type": "Lit", "value": 1.0},
        "right": {"_type": "Lit", "value": 2.0},
    }

    assert genconverter.unstructure(val, Expr) == expected
    assert genconverter.structure(expected, Expr) == val
