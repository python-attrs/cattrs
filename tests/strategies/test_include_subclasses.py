import collections
import typing
import inspect

import attr
import pytest

from cattrs import Converter, override
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn
from cattrs.errors import ClassValidationError
from cattrs.strategies._subclasses import _make_subclasses_tree, include_subclasses


@attr.define
class Parent:
    p: int


@attr.define
class Child1(Parent):
    c1: int


@attr.define
class GrandChild(Child1):
    g: int


@attr.define
class Child2(Parent):
    c2: int


@attr.define
class UnionCompose:
    a: typing.Union[Parent, Child1, Child2, GrandChild]


@attr.define
class NonUnionCompose:
    a: Parent


@attr.define
class UnionContainer:
    a: typing.List[typing.Union[Parent, Child1, Child2, GrandChild]]


@attr.define
class NonUnionContainer:
    a: typing.List[Parent]


@attr.define
class CircularA:
    a: int
    other: "typing.List[CircularA]"


@attr.define
class CircularB(CircularA):
    b: int


IDS_TO_STRUCT_UNSTRUCT = {
    "parent-only": (Parent(1), dict(p=1)),
    "child1-only": (Child1(1, 2), dict(p=1, c1=2)),
    "grandchild-only": (GrandChild(1, 2, 3), dict(p=1, c1=2, g=3)),
    "union-compose-parent": (UnionCompose(Parent(1)), dict(a=dict(p=1))),
    "union-compose-child": (UnionCompose(Child1(1, 2)), dict(a=dict(p=1, c1=2))),
    "union-compose-grandchild": (
        UnionCompose(GrandChild(1, 2, 3)),
        dict(a=(dict(p=1, c1=2, g=3))),
    ),
    "non-union-compose-parent": (NonUnionCompose(Parent(1)), dict(a=dict(p=1))),
    "non-union-compose-child": (NonUnionCompose(Child1(1, 2)), dict(a=dict(p=1, c1=2))),
    "non-union-compose-grandchild": (
        NonUnionCompose(GrandChild(1, 2, 3)),
        dict(a=(dict(p=1, c1=2, g=3))),
    ),
    "union-container": (
        UnionContainer([Parent(1), GrandChild(1, 2, 3)]),
        dict(a=[dict(p=1), dict(p=1, c1=2, g=3)]),
    ),
    "non-union-container": (
        NonUnionContainer([Parent(1), GrandChild(1, 2, 3)]),
        dict(a=[dict(p=1), dict(p=1, c1=2, g=3)]),
    ),
}


@pytest.fixture(params=(True, False), ids=["with-subclasses", "wo-subclasses"])
def conv_w_subclasses(request):
    c = Converter()
    if request.param:
        include_subclasses(Parent, c)

    return c, request.param


@pytest.mark.parametrize(
    "struct_unstruct", IDS_TO_STRUCT_UNSTRUCT.values(), ids=IDS_TO_STRUCT_UNSTRUCT
)
def test_structuring_with_inheritance(
    conv_w_subclasses: typing.Tuple[Converter, bool], struct_unstruct
):
    structured, unstructured = struct_unstruct

    converter, included_subclasses = conv_w_subclasses

    if not included_subclasses and isinstance(
        structured, (NonUnionContainer, NonUnionCompose)
    ):
        pytest.xfail(
            "Cannot structure subclasses if include_subclasses strategy is not used"
        )
    assert converter.structure(unstructured, structured.__class__) == structured

    if structured.__class__ in {Child1, Child2, GrandChild}:
        if not included_subclasses:
            pytest.xfail(
                "Cannot structure subclasses if include_subclasses strategy is not used"
            )
        assert converter.structure(unstructured, Parent) == structured

    if structured.__class__ == GrandChild:
        assert converter.structure(unstructured, Child1) == structured

    if structured.__class__ in {Parent, Child1, Child2}:
        with pytest.raises(ClassValidationError):
            converter.structure(unstructured, GrandChild)


def test_structure_as_union():
    converter = Converter()
    include_subclasses(Parent, converter)
    the_list = [dict(p=1, c1=2)]
    res = converter.structure(the_list, typing.List[typing.Union[Parent, Child1]])
    assert res == [Child1(1, 2)]


def test_circular_reference():
    c = Converter()
    include_subclasses(CircularA, c)
    struct = CircularB(a=1, other=[CircularB(a=2, other=[], b=3)], b=4)
    unstruct = dict(a=1, other=[dict(a=2, other=[], b=3)], b=4)

    res = c.unstructure(struct)
    assert res == unstruct

    res = c.unstructure(struct, CircularA)
    assert res == unstruct

    res = c.structure(unstruct, CircularA)
    assert res == struct


@pytest.mark.parametrize(
    "struct_unstruct", IDS_TO_STRUCT_UNSTRUCT.values(), ids=IDS_TO_STRUCT_UNSTRUCT
)
def test_unstructuring_with_inheritance(
    conv_w_subclasses: typing.Tuple[Converter, bool], struct_unstruct
):
    structured, unstructured = struct_unstruct
    converter, included_subclasses = conv_w_subclasses

    if not included_subclasses:
        if isinstance(structured, (NonUnionContainer, NonUnionCompose)):
            pytest.xfail("Cannot succeed if include_subclasses strategy is not used")

    assert converter.unstructure(structured) == unstructured

    if structured.__class__ in {Child1, Child2, GrandChild}:
        if not included_subclasses:
            pytest.xfail("Cannot succeed if include_subclasses strategy is not used")
        assert converter.unstructure(structured, unstructure_as=Parent) == unstructured

    if structured.__class__ == GrandChild:
        assert converter.unstructure(structured, unstructure_as=Child1) == unstructured


def test_structuring_unstructuring_unknown_subclass():
    @attr.define
    class A:
        a: int

    @attr.define
    class A1(A):
        a1: int

    converter = Converter()
    include_subclasses(A, converter)

    # We define A2 after having created the custom un/structuring functions for A and A1
    @attr.define
    class A2(A1):
        a2: int

    # Even if A2 did not exist, unstructuring_as A works:
    assert converter.unstructure(A2(1, 2, 3), unstructure_as=A) == dict(a=1, a1=2, a2=3)

    # This is an known edge case. The result here is not the correct one! It should be
    # the same as the previous assert. We leave as-is for now and we document that
    # it is preferable to know all subclasses tree before calling include_subclasses
    assert converter.unstructure(A2(1, 2, 3), unstructure_as=A1) == {"a": 1, "a1": 2}

    # This is another edge-case: the result should be A2(1, 2, 3)...
    assert converter.structure(dict(a=1, a1=2, a2=3), A) == A1(1, 2)


def test_structuring_with_subclasses_argument():
    c = Converter()
    include_subclasses(Parent, c, subclasses=(Child1,))

    structured_child, unstructured_child = IDS_TO_STRUCT_UNSTRUCT[
        "non-union-compose-child"
    ]
    assert c.structure(unstructured_child, NonUnionCompose) == structured_child
    assert c.unstructure(structured_child) == unstructured_child

    structured_gchild, unstructured_gchild = IDS_TO_STRUCT_UNSTRUCT[
        "non-union-compose-grandchild"
    ]
    assert c.structure(unstructured_gchild, NonUnionCompose) == structured_child
    assert c.unstructure(structured_gchild) == unstructured_gchild


def test_class_tree_generator():
    class P:
        pass

    class C1(P):
        pass

    class C2(P):
        pass

    class GC1(C2):
        pass

    class GC2(C2):
        pass

    tree_c1 = _make_subclasses_tree(C1)
    assert tree_c1 == [C1]

    tree_c2 = _make_subclasses_tree(C2)
    assert tree_c2 == [C2, GC1, GC2]

    tree_p = _make_subclasses_tree(P)
    assert tree_p == [P, C1, C2, GC1, GC2]
