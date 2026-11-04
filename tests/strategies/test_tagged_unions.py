from typing import Optional, Sequence, Union

import pytest
from attrs import NOTHING, define, field

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

    for instance in (A(), B()):
        data = c.unstructure(instance, Union[A, B])
        original = data.copy()
        assert c.structure(data, Union[A, B]) == instance
        assert data == original


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

    for instance in (A(), B()):
        data = c.unstructure(instance, Union[A, B])
        original = data.copy()
        assert c.structure(data, Union[A, B]) == instance
        assert data == original

    data = {"_type": "unknown"}
    # Repeated unknown tags must keep using the same fallback behavior.
    for _ in range(2):
        assert c.structure(data, Union[A, B]) == A()
        assert data == {"_type": "unknown"}

    data.pop("_type")
    assert c.structure(data, Union[A, B]) == A()


@pytest.mark.parametrize("use_default", [False, True])
@pytest.mark.parametrize("forbid_extra_keys", [False, True])
def test_tag_is_member_field(use_default, forbid_extra_keys):
    """A tag that is also a member field survives structuring and round-trips."""

    @define
    class SpecialDevice:
        hostname: str
        port: int
        type: str

    @define
    class StandardDevice:
        hostname: str
        type: str

    union = SpecialDevice | StandardDevice

    @define
    class Settings:
        device: union

    c = Converter(forbid_extra_keys=forbid_extra_keys)
    configure_tagged_union(
        union,
        c,
        tag_name="type",
        tag_generator={SpecialDevice: "special", StandardDevice: "standard"}.get,
        default=StandardDevice if use_default else NOTHING,
    )

    for payload, expected in (
        (
            {"type": "special", "hostname": "hostname", "port": 1234},
            SpecialDevice("hostname", 1234, "special"),
        ),
        (
            {"type": "standard", "hostname": "hostname"},
            StandardDevice("hostname", "standard"),
        ),
    ):
        data = {"device": payload.copy()}
        result = c.structure(data, Settings)
        assert result == Settings(expected)
        assert data == {"device": payload}
        assert c.unstructure(result) == data


@pytest.mark.parametrize("use_default", [False, True])
@pytest.mark.parametrize("use_alias, tag_name", [(False, "_type"), (True, "type")])
def test_forbid_extra_keys_mixed_members(use_default, use_alias, tag_name):
    """Only members consuming the tag retain it, including private field aliases."""

    @define
    class C:
        _type: str

    union = C | A
    c = Converter(forbid_extra_keys=True, use_alias=use_alias)
    configure_tagged_union(
        union, c, tag_name=tag_name, default=C if use_default else NOTHING
    )

    for data, expected in (({tag_name: "C"}, C("C")), ({tag_name: "A", "a": 1}, A(1))):
        original = data.copy()
        result = c.structure(data, union)
        assert result == expected
        assert data == original
        assert c.unstructure(result, union) == data


def test_forbid_extra_keys_init_false_tag():
    """Fields excluded from init do not consume the tag."""

    @define
    class C:
        type: str = field(init=False, default="unused")

    union = C | A
    c = Converter(forbid_extra_keys=True)
    configure_tagged_union(union, c, tag_name="type")

    assert c.structure({"type": "C"}, union) == C()


def test_forbid_extra_keys_default_with_tag_field():
    """Unknown tags are still removed before invoking the default handler."""

    @define
    class C:
        type: str = "fallback"

    union = C | A
    c = Converter(forbid_extra_keys=True)
    configure_tagged_union(union, c, tag_name="type", default=C)

    assert c.structure({"type": "C"}, union) == C("C")
    assert c.structure({}, union) == C()
    data = {"type": "unknown"}
    for _ in range(2):
        assert c.structure(data, union) == C()
        assert data == {"type": "unknown"}


def test_forbid_extra_keys_custom_member():
    """Members with custom hooks need not be attrs classes or dataclasses."""

    class C:
        pass

    c = Converter(forbid_extra_keys=True)

    @c.register_structure_hook
    def structure_c(val, _) -> C:
        assert val == {}
        return C()

    c.register_unstructure_hook(C, lambda _: {})
    configure_tagged_union(C | A, c)

    assert isinstance(c.structure({"_type": "C"}, C | A), C)


def test_nested_sequence_union():
    @define
    class Top:
        u: Optional[Sequence[Union[A, B]]]

    c = Converter()
    configure_tagged_union(Union[A, B], c)

    data = c.unstructure(Top(u=[B(a="")]), Top)
    c.structure(data, Top)
