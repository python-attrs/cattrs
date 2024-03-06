"""Loading of attrs classes."""

from enum import Enum
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Literal, Union
from unittest.mock import Mock

import pytest
from attrs import NOTHING, Factory, asdict, astuple, define, field, fields, make_class
from hypothesis import assume, given
from hypothesis.strategies import data, lists, sampled_from

from cattrs.converters import BaseConverter, Converter

from .untyped import simple_classes


@given(simple_classes())
def test_structure_simple_from_dict(cl_and_vals):
    """Test structuring non-nested attrs classes dumped with asdict."""
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    obj = cl(*vals, **kwargs)

    dumped = asdict(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=True, min_attrs=1, frozen=False), data())
def test_structure_simple_from_dict_default(cl_and_vals, data):
    """Test structuring non-nested attrs classes with default value."""
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    obj = cl(*vals, **kwargs)
    attrs_with_defaults = [a for a in fields(cl) if a.default is not NOTHING]
    to_remove = data.draw(
        lists(elements=sampled_from(attrs_with_defaults), unique=True)
    )

    for a in to_remove:
        if isinstance(a.default, Factory):
            setattr(obj, a.name, a.default.factory())
        else:
            setattr(obj, a.name, a.default)

    dumped = asdict(obj)

    for a in to_remove:
        del dumped[a.name]

    assert obj == converter.structure(dumped, cl)


@given(simple_classes())
def test_roundtrip(cl_and_vals):
    """We dump the class, then we load it."""
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    obj = cl(*vals, **kwargs)

    dumped = converter.unstructure(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(kw_only=False))
def test_structure_tuple(cl_and_vals):
    """Test loading from a tuple, by registering the loader."""
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    converter.register_structure_hook(cl, converter.structure_attrs_fromtuple)
    obj = cl(*vals, **kwargs)

    dumped = astuple(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_structure_union(cl_and_vals_a, cl_and_vals_b):
    """Structuring of automatically-disambiguable unions works."""
    converter = BaseConverter()
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, kwargs_b = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    if len(a_field_names) > len(common_names):
        obj = cl_a(*vals_a, **kwargs_a)
        dumped = asdict(obj)
        res = converter.structure(dumped, Union[cl_a, cl_b])
        assert isinstance(res, cl_a)
        assert obj == res


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_structure_union_none(cl_and_vals_a, cl_and_vals_b):
    """Structuring of automatically-disambiguable unions works."""
    converter = BaseConverter()
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, _, _ = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    if len(a_field_names) > len(common_names):
        obj = cl_a(*vals_a, **kwargs_a)
        dumped = asdict(obj)
        res = converter.structure(dumped, Union[cl_a, cl_b, None])
        assert isinstance(res, cl_a)
        assert obj == res


@given(simple_classes(), simple_classes())
def test_structure_union_explicit(cl_and_vals_a, cl_and_vals_b):
    """Structuring of manually-disambiguable unions works."""
    converter = BaseConverter()
    cl_a, vals_a, kwargs_a = cl_and_vals_a
    cl_b, vals_b, kwargs_b = cl_and_vals_b

    def dis(obj, _):
        return converter.structure(obj, cl_a)

    converter.register_structure_hook(Union[cl_a, cl_b], dis)

    inst = cl_a(*vals_a, **kwargs_a)

    assert inst == converter.structure(converter.unstructure(inst), Union[cl_a, cl_b])


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_literal(converter_cls):
    """Structuring a class with a literal field works."""
    converter = converter_cls()

    @define
    class ClassWithLiteral:
        literal_field: Literal[4] = 4

    assert converter.structure(
        {"literal_field": 4}, ClassWithLiteral
    ) == ClassWithLiteral(4)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_typing_extensions_literal(converter_cls):
    """Structuring a class with a typing_extensions.Literal field works."""
    converter = converter_cls()
    import typing_extensions

    @define
    class ClassWithLiteral:
        literal_field: typing_extensions.Literal[8] = 8

    assert converter.structure(
        {"literal_field": 8}, ClassWithLiteral
    ) == ClassWithLiteral(8)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_literal_enum(converter_cls):
    """Structuring a class with a literal field works."""
    converter = converter_cls()

    class Foo(Enum):
        FOO = 1
        BAR = 2

    @define
    class ClassWithLiteral:
        literal_field: Literal[Foo.FOO] = Foo.FOO

    assert converter.structure(
        {"literal_field": 1}, ClassWithLiteral
    ) == ClassWithLiteral(Foo.FOO)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_literal_multiple(converter_cls):
    """Structuring a class with a literal field works."""
    converter = converter_cls()

    class Foo(Enum):
        FOO = 7
        FOOFOO = 77

    class Bar(int, Enum):
        BAR = 8
        BARBAR = 88

    @define
    class ClassWithLiteral:
        literal_field: Literal[4, 5, Foo.FOO, Bar.BARBAR] = 4

    assert converter.structure(
        {"literal_field": 4}, ClassWithLiteral
    ) == ClassWithLiteral(4)
    assert converter.structure(
        {"literal_field": 5}, ClassWithLiteral
    ) == ClassWithLiteral(5)

    assert converter.structure(
        {"literal_field": 7}, ClassWithLiteral
    ) == ClassWithLiteral(Foo.FOO)

    cwl = converter.structure({"literal_field": 88}, ClassWithLiteral)
    assert cwl == ClassWithLiteral(Bar.BARBAR)
    assert isinstance(cwl.literal_field, Bar)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_literal_error(converter_cls):
    """Structuring a class with a literal field can raise an error."""
    converter = converter_cls()

    @define
    class ClassWithLiteral:
        literal_field: Literal[4] = 4

    with pytest.raises(Exception):  # noqa: B017
        converter.structure({"literal_field": 3}, ClassWithLiteral)


@pytest.mark.parametrize("converter_cls", [BaseConverter, Converter])
def test_structure_literal_multiple_error(converter_cls):
    """Structuring a class with a literal field can raise an error."""
    converter = converter_cls()

    @define
    class ClassWithLiteral:
        literal_field: Literal[4, 5] = 4

    with pytest.raises(Exception):  # noqa: B017
        converter.structure({"literal_field": 3}, ClassWithLiteral)


def test_structure_fallback_to_attrib_converters(converter):
    """`attrs` converters are called after cattrs processing."""

    @define
    class HasConverter:
        ip: Union[IPv4Address, IPv6Address] = field(converter=ip_address)
        x = field(converter=lambda v: v + 1)
        z: int = field(converter=lambda _: 42)

    inst = converter.structure({"ip": "10.0.0.0", "x": 1, "z": "3"}, HasConverter)

    assert inst.ip == IPv4Address("10.0.0.0")
    assert inst.x == 2
    assert inst.z == 42


@pytest.mark.parametrize("converter_type", [BaseConverter, Converter])
def test_structure_prefers_attrib_converters(converter_type):
    attrib_converter = Mock()
    attrib_converter.side_effect = lambda val: str(val)

    converter = converter_type(prefer_attrib_converters=True)
    cl = make_class(
        "HasConverter",
        {
            # non-built-in type with custom converter
            "ip": field(type=Union[IPv4Address, IPv6Address], converter=ip_address),
            # attribute without type
            "x": field(converter=attrib_converter),
            # built-in types converters
            "y": field(type=int, converter=attrib_converter),
            # attribute with type and default value
            "z": field(type=int, converter=attrib_converter, default=5),
        },
    )

    inst = converter.structure({"ip": "10.0.0.0", "x": 1, "y": 3}, cl)

    assert inst.ip == IPv4Address("10.0.0.0")

    attrib_converter.assert_any_call(1)
    assert inst.x == "1"

    attrib_converter.assert_any_call(3)
    assert inst.y == "3"

    attrib_converter.assert_any_call(5)
    assert inst.z == "5"


@pytest.mark.parametrize("converter_type", [BaseConverter, Converter])
def test_structure_multitier_discriminator_union(converter_type):
    converter = converter_type()

    @define()
    class E:
        op: Literal[1]

    @define()
    class F:
        op: Literal[0]
        t: Literal["MESSAGE_CREATE"]

    @define()
    class G:
        op: Literal[0]
        t: Literal["MESSAGE_UPDATE"]

    inst = converter.structure({"op": 1}, Union[E, F, G])
    assert isinstance(inst, E)

    inst = converter.structure({"op": 0, "t": "MESSAGE_CREATE"}, Union[E, F, G])
    assert isinstance(inst, F)
