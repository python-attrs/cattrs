import uuid
import zoneinfo
from functools import partial
from platform import python_implementation

from attrs import define, fields
from bson import UuidRepresentation
from hypothesis import given
from hypothesis.strategies import (
    DrawFn,
    builds,
    complex_numbers,
    composite,
    timezone_keys,
    uuids,
)
from pytest import fixture, mark, skip

from cattrs import Converter
from cattrs.preconf import has_format
from cattrs.strategies import register_extra_types

# converters

# isort: off
from cattrs.preconf import bson
from cattrs.preconf import cbor2
from cattrs.preconf import json
from cattrs.preconf import msgpack
from cattrs.preconf import pyyaml
from cattrs.preconf import tomlkit
from cattrs.preconf import ujson

if python_implementation() != "PyPy":
    from cattrs.preconf import msgspec
    from cattrs.preconf import orjson
else:
    msgspec = "msgspec"
    orjson = "orjson"

PRECONF_MODULES = [bson, cbor2, json, msgpack, msgspec, orjson, pyyaml, tomlkit, ujson]
# isort: on


@define
class Extras:
    complex: complex
    uuid: uuid.UUID
    zoneinfo: zoneinfo.ZoneInfo


EXTRA_TYPES = {attr.name: attr.type for attr in fields(Extras)}


@composite
def extras(draw: DrawFn):
    return Extras(
        complex=draw(complex_numbers(allow_infinity=True, allow_nan=False)),
        uuid=draw(uuids(allow_nil=True)),
        zoneinfo=draw(builds(zoneinfo.ZoneInfo, timezone_keys())),
    )


# converters


@fixture(scope="session")
def raw_converter(converter_cls) -> Converter:
    """Raw BaseConverter and Converter."""
    conv = converter_cls()
    register_extra_types(conv, *EXTRA_TYPES.values())
    return conv


@fixture(scope="session", params=PRECONF_MODULES)
def preconf_converter(request) -> Converter:
    """All preconfigured converters."""
    if isinstance(request.param, str):
        skip(f'Converter "{request.param}" is unavailable for current implementation')

    conv = request.param.make_converter()
    register_extra_types(conv, *EXTRA_TYPES.values())
    return conv


@fixture(scope="session", params=[None, *PRECONF_MODULES])
def any_converter(request) -> Converter:
    """Global converter and all preconfigured converters."""
    if isinstance(request.param, str):
        skip(f'Converter "{request.param}" is unavailable for current implementation')

    conv = request.param.make_converter() if request.param else Converter()
    register_extra_types(conv, *EXTRA_TYPES.values())
    return conv


# common tests


@given(extras())
def test_restructure_attrs(any_converter, item: Extras):
    """Extra types as attributes can be unstructured and restructured."""
    assert any_converter.structure(any_converter.unstructure(item), Extras) == item


@given(extras())
def test_restructure_values(any_converter, item: Extras):
    """Extra types as standalone values can be unstructured and restructured."""
    for attr, cl in EXTRA_TYPES.items():
        value = getattr(item, attr)
        assert any_converter.structure(any_converter.unstructure(value), cl) == value


@given(extras())
def test_restructure_optional(any_converter, item: Extras):
    """Extra types as optional standalone values can be structured."""
    for attr, cl in EXTRA_TYPES.items():
        value = getattr(item, attr)
        assert any_converter.structure(None, cl | None) is None
        assert (
            any_converter.structure(any_converter.unstructure(value), cl | None)
            == value
        )


@given(extras())
def test_dumpload_attrs(preconf_converter, item: Extras):
    """Extra types as attributes can be dumped/loaded by preconfigured converters."""
    if has_format(preconf_converter, "bson"):
        # BsonConverter requires explicit UUID representation
        codec_options = bson.DEFAULT_CODEC_OPTIONS.with_options(
            uuid_representation=UuidRepresentation.STANDARD
        )
        dumps = partial(preconf_converter.dumps, codec_options=codec_options)
        loads = partial(preconf_converter.loads, codec_options=codec_options)
    elif has_format(preconf_converter, "msgspec"):
        # MsgspecJsonConverter can be used with dumps/loads factories for extra types
        dumps = preconf_converter.get_dumps_hook(Extras)
        loads = lambda v, cl: preconf_converter.get_loads_hook(cl)(v)  # noqa: E731
    else:
        dumps = preconf_converter.dumps
        loads = preconf_converter.loads
    # test
    assert loads(dumps(item), Extras) == item


# builtins.complex


@mark.parametrize("unstructured,structured", [([1.0, 0.0], complex(1, 0))])
def test_specific_complex(raw_converter, unstructured, structured) -> None:
    """Raw converter structures complex."""
    assert raw_converter.structure(unstructured, complex) == structured


# uuid.UUID

UUID_NIL = uuid.UUID(bytes=b"\x00" * 16)


@mark.parametrize(
    "value",
    (
        UUID_NIL,  # passthrough
        b"\x00" * 16,
        0,
        "00000000000000000000000000000000",
        "00000000-0000-0000-0000-000000000000",
        "{00000000000000000000000000000000}",
        "{00000000-0000-0000-0000-000000000000}",
        "urn:uuid:00000000000000000000-000000000000",
        "urn:uuid:00000000-0000-0000-0000-000000000000",
    ),
)
def test_specific_uuid(raw_converter, value) -> None:
    """Raw converter structures from all formats supported by uuid.UUID."""
    assert raw_converter.structure(value, uuid.UUID) == UUID_NIL


# zoneinfo.ZoneInfo


@mark.parametrize("value", ("EET", "Europe/Kiev"))
def test_specific_zoneinfo(raw_converter, value) -> None:
    """Raw converter structures zoneinfo.ZoneInfo."""
    assert raw_converter.structure(value, zoneinfo.ZoneInfo) == zoneinfo.ZoneInfo(value)
