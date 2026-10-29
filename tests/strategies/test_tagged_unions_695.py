from __future__ import annotations

from copy import deepcopy

import pytest
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


def test_nullable_type_alias(converter: BaseConverter):
    """Type aliases preserve explicit nullable tagged union handling."""
    type AOrBOrNone = A | B | None

    configure_tagged_union(AOrBOrNone, converter)

    assert converter.unstructure(None, AOrBOrNone) is None
    assert converter.structure(None, AOrBOrNone) is None
    assert converter.unstructure(A(1), AOrBOrNone) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), AOrBOrNone) == {"_type": "B", "a": "1"}
    assert converter.structure({"_type": "A", "a": 1}, AOrBOrNone) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, AOrBOrNone) == B("1")


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


@define
class Node:
    value: int
    next: Chain


type Chain = Node | None


@pytest.mark.parametrize("detailed_validation", [True, False])
@pytest.mark.parametrize("outer_tag", [None, "unknown", "Node"])
def test_recursive_nullable_alias_default(detailed_validation: bool, outer_tag):
    """Default members use the nullable tagged hook for recursive fields."""
    converter = Converter(
        forbid_extra_keys=True, detailed_validation=detailed_validation
    )
    configure_tagged_union(Chain, converter, default=Node)

    data = {"value": 1, "next": {"_type": "Node", "value": 2, "next": None}}
    if outer_tag is not None:
        data["_type"] = outer_tag
    original = deepcopy(data)

    structured = converter.structure(data, Chain)
    assert structured == Node(1, Node(2, None))
    assert data == original

    expected = {
        "_type": "Node",
        "value": 1,
        "next": {"_type": "Node", "value": 2, "next": None},
    }
    unstructured = converter.unstructure(structured, Chain)
    assert unstructured == expected
    assert converter.structure(unstructured, Chain) == structured
    assert unstructured == expected
