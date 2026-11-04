from typing import Optional, Sequence, Union

from attrs import define

from cattrs import BaseConverter, Converter
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


def test_default_member(converter: BaseConverter) -> None:
    """Tagged unions can have default members."""
    union = Union[A, B]
    configure_tagged_union(union, converter, default=A)
    assert converter.unstructure(A(1), union) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), union) == {"_type": "B", "a": "1"}

    # No tag, so should structure as A.
    assert converter.structure({"a": 1}, union) == A(1)
    # Wrong tag, so should again structure as A.
    assert converter.structure({"_type": "C", "a": 1}, union) == A(1)

    assert converter.structure({"_type": "A", "a": 1}, union) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, union) == B("1")


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


def test_forbid_extra_keys():
    """The strategy works when converters forbid extra keys."""

    @define
    class A:
        pass

    @define
    class B:
        pass

    c = Converter(forbid_extra_keys=True)
    configure_tagged_union(Union[A, B], c)

    data = c.unstructure(A(), Union[A, B])
    c.structure(data, Union[A, B])


def test_forbid_extra_keys_default():
    """The strategy works when converters forbid extra keys."""

    @define
    class A:
        pass

    @define
    class B:
        pass

    c = Converter(forbid_extra_keys=True)
    configure_tagged_union(Union[A, B], c, default=A)

    data = c.unstructure(A(), Union[A, B])
    assert c.structure(data, Union[A, B]) == A()

    data.pop("_type")
    assert c.structure(data, Union[A, B]) == A()


def test_nested_sequence_union():
    @define
    class Top:
        u: Optional[Sequence[Union[A, B]]]

    c = Converter()
    configure_tagged_union(Union[A, B], c)

    data = c.unstructure(Top(u=[B(a="")]), Top)
    c.structure(data, Top)


def test_optional_union(converter: BaseConverter) -> None:
    """The union extended with `None` is handled too.

    Regression test for https://github.com/python-attrs/cattrs/issues/345
    """
    union = Union[A, B]
    configure_tagged_union(union, converter)

    optional = Optional[union]

    assert converter.unstructure(A(1), optional) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), optional) == {"_type": "B", "a": "1"}
    assert converter.unstructure(None, optional) is None

    assert converter.structure({"_type": "A", "a": 1}, optional) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, optional) == B("1")
    assert converter.structure(None, optional) is None


def test_optional_union_in_class(converter: BaseConverter) -> None:
    """Optional tagged unions work as class fields, in both spellings."""
    union = Union[A, B]
    configure_tagged_union(union, converter)

    @define
    class Holder:
        c: Union[A, B, None]

    @define
    class TypingHolder:
        c: Optional[Union[A, B]]

    assert converter.unstructure(Holder(B("1"))) == {"c": {"_type": "B", "a": "1"}}
    assert converter.unstructure(Holder(None)) == {"c": None}
    assert converter.structure({"c": {"_type": "B", "a": "1"}}, Holder) == Holder(
        B("1")
    )
    assert converter.structure({"c": None}, Holder) == Holder(None)

    assert converter.unstructure(TypingHolder(B("1"))) == {
        "c": {"_type": "B", "a": "1"}
    }
    assert converter.structure({"c": None}, TypingHolder) == TypingHolder(None)
