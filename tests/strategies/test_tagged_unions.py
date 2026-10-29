from dataclasses import dataclass
from typing import Optional, Sequence, Union

import pytest
from attrs import define

from cattrs import BaseConverter, ClassValidationError, Converter
from cattrs.strategies import configure_tagged_union


@define
class A:
    a: int


@define
class B:
    a: str


def test_defaults(converter: BaseConverter) -> None:
    """Defaults should work."""
    union = Union[A, B]
    configure_tagged_union(union, converter)

    assert converter.unstructure(A(1), union) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), union) == {"_type": "B", "a": "1"}

    assert converter.structure({"_type": "A", "a": 1}, union) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, union) == B("1")


@pytest.mark.parametrize("container_decorator", [define, dataclass])
def test_nullable_union(converter: BaseConverter, container_decorator) -> None:
    """Nullable tagged unions preserve tags in attrs and dataclass fields."""
    union = Union[A, B, None]

    @container_decorator
    class Container:
        value: Union[A, B, None]

    configure_tagged_union(
        union, converter, tag_name="kind", tag_generator={A: "a", B: "b"}.__getitem__
    )

    for value, expected in (
        (None, None),
        (A(1), {"kind": "a", "a": 1}),
        (B("1"), {"kind": "b", "a": "1"}),
    ):
        data = converter.unstructure(value, union)
        assert data == expected
        assert converter.structure(data, union) == value
        assert data == expected

        instance = Container(value)
        data = converter.unstructure(instance)
        assert data == {"value": expected}
        assert converter.structure(data, Container) == instance
        assert data == {"value": expected}


def test_optional_class(converter: BaseConverter) -> None:
    """A tagged union may contain only one class alongside None."""
    union = Optional[A]
    configure_tagged_union(union, converter)

    assert converter.unstructure(None, union) is None
    assert converter.structure(None, union) is None
    assert converter.unstructure(A(1), union) == {"_type": "A", "a": 1}
    assert converter.structure({"_type": "A", "a": 1}, union) == A(1)


def test_tag_name(converter: BaseConverter) -> None:
    """Tag names are customizable."""
    union = Union[A, B]
    tag_name = "t"
    configure_tagged_union(union, converter, tag_name=tag_name)

    assert converter.unstructure(A(1), union) == {tag_name: "A", "a": 1}
    assert converter.unstructure(B("1"), union) == {tag_name: "B", "a": "1"}

    assert converter.structure({tag_name: "A", "a": 1}, union) == A(1)
    assert converter.structure({tag_name: "B", "a": 1}, union) == B("1")


def test_tag_generator(converter: BaseConverter) -> None:
    """Tag values are customizable using a callable."""
    union = Union[A, B]
    configure_tagged_union(
        union, converter, tag_generator=lambda t: f"{t.__module__}.{t.__name__}"
    )

    assert converter.unstructure(A(1), union) == {
        "_type": "tests.strategies.test_tagged_unions.A",
        "a": 1,
    }
    assert converter.unstructure(B("1"), union) == {
        "_type": "tests.strategies.test_tagged_unions.B",
        "a": "1",
    }

    assert converter.structure(
        {"_type": "tests.strategies.test_tagged_unions.A", "a": 1}, union
    ) == A(1)
    assert converter.structure(
        {"_type": "tests.strategies.test_tagged_unions.B", "a": 1}, union
    ) == B("1")


def test_tag_generator_dict(converter: BaseConverter) -> None:
    """Tag values are customizable using a dict."""
    union = Union[A, B]
    configure_tagged_union(
        union,
        converter,
        tag_generator={cl: f"type:{cl.__name__}" for cl in union.__args__}.get,
    )

    assert converter.unstructure(A(1), union) == {"_type": "type:A", "a": 1}
    assert converter.unstructure(B("1"), union) == {"_type": "type:B", "a": "1"}

    assert converter.structure({"_type": "type:A", "a": 1}, union) == A(1)
    assert converter.structure({"_type": "type:B", "a": 1}, union) == B("1")


@pytest.mark.parametrize("nullable", [False, True])
def test_default_member(converter: BaseConverter, nullable: bool) -> None:
    """Tagged unions can have default members."""
    union = Union[A, B, None] if nullable else Union[A, B]
    configure_tagged_union(union, converter, default=A)
    assert converter.unstructure(A(1), union) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), union) == {"_type": "B", "a": "1"}

    # No tag, so should structure as A.
    assert converter.structure({"a": 1}, union) == A(1)
    # Wrong tag, so should again structure as A.
    assert converter.structure({"_type": "C", "a": 1}, union) == A(1)

    assert converter.structure({"_type": "A", "a": 1}, union) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, union) == B("1")

    if nullable:
        assert converter.unstructure(None, union) is None
        assert converter.structure(None, union) is None


def test_default_member_with_tag(converter: BaseConverter) -> None:
    """Members can access the tags, if not `forbid_extra_keys`."""

    @define
    class C:
        _type: str = ""

    union = Union[A, B, C]
    configure_tagged_union(union, converter, default=C)
    assert converter.unstructure(A(1), union) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), union) == {"_type": "B", "a": "1"}

    # No tag, so should structure as C.
    assert converter.structure({"a": 1}, union) == C()
    # Wrong tag, so should again structure as C.
    assert converter.structure({"_type": "D", "a": 1}, union) == C("D")

    assert converter.structure({"_type": "A", "a": 1}, union) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, union) == B("1")
    assert converter.structure({"_type": "C", "a": 1}, union) == C("C")


def test_default_member_validation(converter: BaseConverter) -> None:
    """Default members are structured properly.."""
    union = Union[A, B]
    configure_tagged_union(union, converter, default=A)

    # A.a should be coerced to an int.
    assert converter.structure({"_type": "A", "a": "1"}, union) == A(1)


@pytest.mark.parametrize("nullable", [False, True])
def test_forbid_extra_keys(nullable: bool):
    """The strategy works when converters forbid extra keys."""

    @define
    class A:
        pass

    @define
    class B:
        pass

    c = Converter(forbid_extra_keys=True)
    union = Union[A, B, None] if nullable else Union[A, B]
    configure_tagged_union(union, c)

    data = c.unstructure(A(), union)
    assert c.structure(data, union) == A()
    assert data == {"_type": "A"}

    data = {"_type": "A", "extra": 1}
    with pytest.raises(ClassValidationError):
        c.structure(data, union)
    assert data == {"_type": "A", "extra": 1}

    if nullable:
        assert c.unstructure(None, union) is None
        assert c.structure(None, union) is None


@pytest.mark.parametrize("nullable", [False, True])
def test_forbid_extra_keys_default(nullable: bool):
    """The strategy works when converters forbid extra keys."""

    @define
    class A:
        pass

    @define
    class B:
        pass

    c = Converter(forbid_extra_keys=True)
    union = Union[A, B, None] if nullable else Union[A, B]
    configure_tagged_union(union, c, default=A)

    data = c.unstructure(A(), union)
    assert c.structure(data, union) == A()
    assert data == {"_type": "A"}

    data.pop("_type")
    assert c.structure(data, union) == A()
    assert data == {}

    data = {"_type": "unknown"}
    assert c.structure(data, union) == A()
    assert data == {"_type": "unknown"}

    for data in ({"_type": "A", "extra": 1}, {"extra": 1}):
        original = data.copy()
        with pytest.raises(ClassValidationError):
            c.structure(data, union)
        assert data == original

    if nullable:
        assert c.unstructure(None, union) is None
        assert c.structure(None, union) is None


def test_nested_sequence_union():
    @define
    class Top:
        u: Optional[Sequence[Union[A, B]]]

    c = Converter()
    configure_tagged_union(Union[A, B], c)

    data = c.unstructure(Top(u=[B(a="")]), Top)
    c.structure(data, Top)
