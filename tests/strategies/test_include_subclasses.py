import typing
from copy import deepcopy
from functools import partial

import pytest
from attrs import define

from cattrs import Converter, override
from cattrs.errors import ClassValidationError, StructureHandlerNotFoundError
from cattrs.strategies import configure_tagged_union, include_subclasses

T = typing.TypeVar("T")


@define
class Parent:
    p: int


@define
class Child1(Parent):
    c1: int


@define
class GrandChild(Child1):
    g: int


@define
class Child2(Parent):
    c2: int


@define
class UnionCompose:
    a: typing.Union[Parent, Child1, Child2, GrandChild]


@define
class NonUnionCompose:
    a: Parent


@define
class UnionContainer:
    a: typing.List[typing.Union[Parent, Child1, Child2, GrandChild]]


@define
class NonUnionContainer:
    a: typing.List[Parent]


@define
class CircularA:
    a: int
    other: "typing.List[CircularA]"


@define
class CircularB(CircularA):
    b: int


def _remove_type_name(unstructured: typing.Union[typing.Dict, typing.List]):
    if isinstance(unstructured, list):
        iterator = unstructured
    elif isinstance(unstructured, dict):
        if "type_name" in unstructured:
            unstructured.pop("type_name")
        iterator = unstructured.values()
    for item in iterator:
        if isinstance(item, (list, dict)):
            _remove_type_name(item)
    return unstructured


IDS_TO_STRUCT_UNSTRUCT = {
    "parent-only": (Parent(1), {"p": 1, "type_name": "Parent"}),
    "child1-only": (Child1(1, 2), {"p": 1, "c1": 2, "type_name": "Child1"}),
    "child2-only": (Child2(1, 2), {"p": 1, "c2": 2, "type_name": "Child2"}),
    "grandchild-only": (
        GrandChild(1, 2, 3),
        {"p": 1, "c1": 2, "g": 3, "type_name": "GrandChild"},
    ),
    "union-compose-parent": (
        UnionCompose(Parent(1)),
        {"a": {"p": 1, "type_name": "Parent"}},
    ),
    "union-compose-child": (
        UnionCompose(Child1(1, 2)),
        {"a": {"p": 1, "c1": 2, "type_name": "Child1"}},
    ),
    "union-compose-grandchild": (
        UnionCompose(GrandChild(1, 2, 3)),
        {"a": ({"p": 1, "c1": 2, "g": 3, "type_name": "GrandChild"})},
    ),
    "non-union-compose-parent": (
        NonUnionCompose(Parent(1)),
        {"a": {"p": 1, "type_name": "Parent"}},
    ),
    "non-union-compose-child": (
        NonUnionCompose(Child1(1, 2)),
        {"a": {"p": 1, "c1": 2, "type_name": "Child1"}},
    ),
    "non-union-compose-grandchild": (
        NonUnionCompose(GrandChild(1, 2, 3)),
        {"a": ({"p": 1, "c1": 2, "g": 3, "type_name": "GrandChild"})},
    ),
    "union-container": (
        UnionContainer([Parent(1), GrandChild(1, 2, 3)]),
        {
            "a": [
                {"p": 1, "type_name": "Parent"},
                {"p": 1, "c1": 2, "g": 3, "type_name": "GrandChild"},
            ]
        },
    ),
    "non-union-container": (
        NonUnionContainer([Parent(1), GrandChild(1, 2, 3)]),
        {
            "a": [
                {"p": 1, "type_name": "Parent"},
                {"p": 1, "c1": 2, "g": 3, "type_name": "GrandChild"},
            ]
        },
    ),
}


@pytest.fixture(
    params=["with-subclasses", "with-subclasses-and-tagged-union", "wo-subclasses"]
)
def conv_w_subclasses(request):
    c = Converter()
    if request.param == "with-subclasses":
        include_subclasses(Parent, c)
        include_subclasses(CircularA, c)
    elif request.param == "with-subclasses-and-tagged-union":
        union_strategy = partial(configure_tagged_union, tag_name="type_name")
        include_subclasses(Parent, c, union_strategy=union_strategy)
        include_subclasses(CircularA, c, union_strategy=union_strategy)

    return c, request.param


@pytest.mark.parametrize(
    "struct_unstruct", IDS_TO_STRUCT_UNSTRUCT.values(), ids=IDS_TO_STRUCT_UNSTRUCT
)
def test_structuring_with_inheritance(
    conv_w_subclasses: tuple[Converter, bool], struct_unstruct
) -> None:
    structured, unstructured = struct_unstruct

    converter, included_subclasses_param = conv_w_subclasses
    if included_subclasses_param != "with-subclasses-and-tagged-union":
        unstructured = _remove_type_name(deepcopy(unstructured))

    if "wo-subclasses" in included_subclasses_param and isinstance(
        structured, (NonUnionContainer, NonUnionCompose)
    ):
        pytest.xfail(
            "Cannot structure subclasses if include_subclasses strategy is not used"
        )
    assert converter.structure(unstructured, structured.__class__) == structured

    if structured.__class__ in {Child1, Child2, GrandChild}:
        if "wo-subclasses" in included_subclasses_param:
            pytest.xfail(
                "Cannot structure subclasses if include_subclasses strategy is not used"
            )
        assert converter.structure(unstructured, Parent) == structured

    if structured.__class__ == GrandChild:
        assert converter.structure(unstructured, Child1) == structured

    if structured.__class__ in {Parent, Child1, Child2}:
        with pytest.raises(ClassValidationError):
            _ = converter.structure(unstructured, GrandChild)


def test_structure_as_union():
    converter = Converter()
    include_subclasses(Parent, converter)
    the_list = [{"p": 1, "c1": 2}]
    res = converter.structure(the_list, typing.List[typing.Union[Parent, Child1]])
    assert res == [Child1(1, 2)]


def test_circular_reference(conv_w_subclasses):
    c, included_subclasses_param = conv_w_subclasses

    struct = CircularB(a=1, other=[CircularB(a=2, other=[], b=3)], b=4)
    unstruct = {
        "a": 1,
        "other": [{"a": 2, "other": [], "b": 3, "type_name": "CircularB"}],
        "b": 4,
        "type_name": "CircularB",
    }

    if included_subclasses_param != "with-subclasses-and-tagged-union":
        unstruct = _remove_type_name(unstruct)

    if "wo-subclasses" in included_subclasses_param:
        pytest.xfail("Cannot succeed if include_subclasses strategy is not used")

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
    conv_w_subclasses: tuple[Converter, bool], struct_unstruct
):
    structured, unstructured = struct_unstruct
    converter, included_subclasses_param = conv_w_subclasses

    if "wo-subclasses" in included_subclasses_param and isinstance(
        structured, (NonUnionContainer, NonUnionCompose)
    ):
        pytest.xfail("Cannot succeed if include_subclasses strategy is not used")

    if included_subclasses_param != "with-subclasses-and-tagged-union":
        unstructured = _remove_type_name(deepcopy(unstructured))

    assert converter.unstructure(structured) == unstructured

    if structured.__class__ in {Child1, Child2, GrandChild}:
        if "wo-subclasses" in included_subclasses_param:
            pytest.xfail("Cannot succeed if include_subclasses strategy is not used")
        assert converter.unstructure(structured, unstructure_as=Parent) == unstructured

    if structured.__class__ == GrandChild:
        assert converter.unstructure(structured, unstructure_as=Child1) == unstructured


def test_structuring_unstructuring_unknown_subclass():
    @define
    class A:
        a: int

    @define
    class A1(A):
        a1: int

    converter = Converter()
    include_subclasses(A, converter)

    # We define A2 after having created the custom un/structuring functions for A and A1
    @define
    class A2(A1):
        a2: int

    # Even if A2 did not exist, unstructuring_as A works:
    assert converter.unstructure(A2(1, 2, 3), unstructure_as=A) == {
        "a": 1,
        "a1": 2,
        "a2": 3,
    }

    # As well as when unstructuring as A1, in other words, unstructuring works for
    # unknown classes.
    assert converter.unstructure(A2(1, 2, 3), unstructure_as=A1) == {
        "a": 1,
        "a1": 2,
        "a2": 3,
    }

    # But as expected, structuring unknown classes as their parent fails to give the
    # correct answer. This is a documented drawback, we just confirm it.
    assert converter.structure({"a": 1, "a1": 2, "a2": 3}, A) == A1(1, 2)


def test_structuring_with_subclasses_argument():
    c = Converter()
    include_subclasses(Parent, c, subclasses=(Child1,))

    structured_child, unstructured_child = IDS_TO_STRUCT_UNSTRUCT[
        "non-union-compose-child"
    ]
    unstructured_child = _remove_type_name(deepcopy(unstructured_child))
    assert c.structure(unstructured_child, NonUnionCompose) == structured_child
    assert c.unstructure(structured_child) == unstructured_child

    structured_gchild, unstructured_gchild = IDS_TO_STRUCT_UNSTRUCT[
        "non-union-compose-grandchild"
    ]
    unstructured_gchild = _remove_type_name(deepcopy(unstructured_gchild))
    assert c.structure(unstructured_gchild, NonUnionCompose) == structured_child
    assert c.unstructure(structured_gchild) == unstructured_gchild


@pytest.mark.parametrize(
    "struct_unstruct", ["parent-only", "child1-only", "child2-only", "grandchild-only"]
)
@pytest.mark.parametrize(
    "with_union_strategy",
    [True, False],
    ids=["with-union-strategy", "wo-union-strategy"],
)
def test_overrides(with_union_strategy: bool, struct_unstruct: str):
    c = Converter()
    union_strategy = (
        partial(configure_tagged_union, tag_name="type_name")
        if with_union_strategy
        else None
    )
    include_subclasses(
        Parent, c, overrides={"p": override(rename="u")}, union_strategy=union_strategy
    )

    structured, unstructured = IDS_TO_STRUCT_UNSTRUCT[struct_unstruct]
    unstructured = unstructured.copy()
    val = unstructured.pop("p")
    unstructured["u"] = val
    if not with_union_strategy:
        unstructured.pop("type_name")

    assert c.unstructure(structured) == unstructured
    assert c.structure(unstructured, Parent) == structured
    assert c.structure(unstructured, structured.__class__) == structured


def test_no_parent_classes(genconverter: Converter):
    """Test an edge condition when a union strategy is used.

    The class being registered has no subclasses.
    """

    @define
    class A:
        a: int

    include_subclasses(A, genconverter, union_strategy=configure_tagged_union)

    assert genconverter.structure({"a": 1}, A) == A(1)


def test_cyclic_classes(genconverter: Converter):
    """A cyclic reference case from issue #542."""

    @define
    class Base:
        pass

    @define
    class Subclass1(Base):
        b: str
        a: Base

    @define
    class Subclass2(Base):
        b: str

    include_subclasses(Base, genconverter, union_strategy=configure_tagged_union)

    assert genconverter.structure(
        {"b": "a", "_type": "Subclass1", "a": {"b": "c", "_type": "Subclass2"}}, Base
    ) == Subclass1("a", Subclass2("c"))


def test_cycles_classes_2(genconverter: Converter):
    """A cyclic reference case from #430."""

    @define
    class A:
        x: int

    @define
    class Derived(A):
        d: A

    include_subclasses(A, genconverter, union_strategy=configure_tagged_union)

    assert genconverter.structure(
        [
            {
                "x": 9,
                "d": {"x": 99, "d": {"x": 999, "_type": "A"}, "_type": "Derived"},
                "_type": "Derived",
            }
        ],
        list[A],
    ) == [Derived(9, Derived(99, A(999)))]


def test_unsupported_class(genconverter: Converter):
    """Non-attrs/dataclass classes raise proper errors."""

    class NewParent:
        """Not an attrs class."""

        a: int

    @define
    class NewChild(NewParent):
        pass

    @define
    class NewChild2(NewParent):
        pass

    genconverter.register_structure_hook(NewParent, lambda v, _: NewParent(v))

    with pytest.raises(StructureHandlerNotFoundError):
        include_subclasses(NewParent, genconverter)


def test_parents_with_generics(genconverter: Converter):
    """Ensure proper handling of generic parents #648."""

    @define
    class GenericParent(typing.Generic[T]):
        p: T

    @define
    class Child1G(GenericParent[str]):
        c: str

    include_subclasses(GenericParent[str], genconverter)

    assert genconverter.structure({"p": 5, "c": 5}, GenericParent[str]) == Child1G(
        "5", "5"
    )
