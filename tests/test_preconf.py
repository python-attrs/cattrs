from datetime import datetime, timezone
from enum import Enum, IntEnum, unique
from json import dumps as json_dumps
from json import loads as json_loads
from platform import python_implementation
from typing import Dict, List

import pytest
from attr import define
from bson import CodecOptions, ObjectId
from hypothesis import given
from hypothesis.strategies import (
    binary,
    booleans,
    characters,
    composite,
    datetimes,
    dictionaries,
    floats,
    frozensets,
    integers,
    just,
    lists,
    sets,
    text,
)

from cattrs._compat import (
    Counter,
    FrozenSet,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
    TupleSubscriptable,
)
from cattrs.preconf.bson import make_converter as bson_make_converter
from cattrs.preconf.json import make_converter as json_make_converter
from cattrs.preconf.msgpack import make_converter as msgpack_make_converter
from cattrs.preconf.pyyaml import make_converter as pyyaml_make_converter
from cattrs.preconf.tomlkit import make_converter as tomlkit_make_converter
from cattrs.preconf.ujson import make_converter as ujson_make_converter


@define
class Everything:
    @unique
    class AnIntEnum(IntEnum):
        A = 1

    @unique
    class AStringEnum(str, Enum):
        A = "a"

    string: str
    bytes: bytes
    an_int: int
    a_float: float
    a_dict: Dict[str, int]
    a_list: List[int]
    a_homogenous_tuple: TupleSubscriptable[int, ...]
    a_hetero_tuple: TupleSubscriptable[str, int, float]
    a_counter: Counter[str]
    a_mapping: Mapping[int, float]
    a_mutable_mapping: MutableMapping[float, str]
    a_sequence: Sequence[float]
    a_mutable_sequence: MutableSequence[str]
    a_set: Set[float]
    a_mutable_set: MutableSet[int]
    a_frozenset: FrozenSet[str]
    an_int_enum: AnIntEnum
    a_str_enum: AStringEnum
    a_datetime: datetime
    a_string_enum_dict: Dict[AStringEnum, int]
    a_bytes_dict: Dict[bytes, bytes]


@composite
def everythings(
    draw,
    min_int=None,
    max_int=None,
    allow_inf=True,
    allow_null_bytes_in_keys=True,
    allow_control_characters_in_values=True,
    min_key_length=0,
    allow_datetime_microseconds=True,
    key_blacklist_characters=[],
):
    key_text = text(
        characters(
            blacklist_categories=("Cs",) if allow_null_bytes_in_keys else ("Cs", "Cc"),
            blacklist_characters=key_blacklist_characters,
        ),
        min_size=min_key_length,
    )
    strings = text(
        characters(
            blacklist_categories=("Cs",)
            if allow_control_characters_in_values
            else ("Cs", "Cc")
        )
    )
    dts = datetimes(
        min_value=datetime(1970, 1, 1),
        max_value=datetime(2038, 1, 1),
        timezones=just(timezone.utc),
    )
    if not allow_datetime_microseconds:
        dts = dts.map(
            lambda d: datetime(
                d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=d.tzinfo
            )
        )
    return Everything(
        draw(strings),
        draw(binary()),
        draw(integers(min_value=min_int, max_value=max_int)),
        draw(floats(allow_nan=False, allow_infinity=allow_inf)),
        draw(dictionaries(key_text, integers(min_value=min_int, max_value=max_int))),
        draw(lists(integers(min_value=min_int, max_value=max_int))),
        tuple(draw(lists(integers(min_value=min_int, max_value=max_int)))),
        (
            draw(strings),
            draw(integers(min_value=min_int, max_value=max_int)),
            draw(floats(allow_nan=False, allow_infinity=allow_inf)),
        ),
        Counter(
            draw(dictionaries(key_text, integers(min_value=min_int, max_value=max_int)))
        ),
        draw(
            dictionaries(
                integers(min_value=min_int, max_value=max_int),
                floats(allow_nan=False, allow_infinity=allow_inf),
            )
        ),
        draw(dictionaries(floats(allow_nan=False, allow_infinity=allow_inf), strings)),
        draw(lists(floats(allow_nan=False, allow_infinity=allow_inf))),
        draw(lists(strings)),
        draw(sets(floats(allow_nan=False, allow_infinity=allow_inf))),
        draw(sets(integers(min_value=min_int, max_value=max_int))),
        draw(frozensets(strings)),
        Everything.AnIntEnum.A,
        Everything.AStringEnum.A,
        draw(dts),
        draw(
            dictionaries(
                just(Everything.AStringEnum.A),
                integers(min_value=min_int, max_value=max_int),
            )
        ),
        draw(dictionaries(binary(min_size=min_key_length), binary())),
    )


@given(everythings())
def test_stdlib_json(everything: Everything):
    converter = json_make_converter()
    assert (
        converter.structure(
            json_loads(json_dumps(converter.unstructure(everything))), Everything
        )
        == everything
    )


@given(everythings())
def test_stdlib_json_converter(everything: Everything):
    converter = json_make_converter()
    assert converter.loads(converter.dumps(everything), Everything) == everything


@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    )
)
def test_ujson(everything: Everything):
    from ujson import dumps as ujson_dumps
    from ujson import loads as ujson_loads

    converter = ujson_make_converter()
    raw = ujson_dumps(converter.unstructure(everything))
    assert converter.structure(ujson_loads(raw), Everything) == everything


@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    )
)
def test_ujson_converter(everything: Everything):
    converter = ujson_make_converter()
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


@pytest.mark.skipif(python_implementation() == "PyPy", reason="no orjson on PyPy")
@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    ),
    booleans(),
)
def test_orjson(everything: Everything, detailed_validation: bool):
    from orjson import dumps as orjson_dumps
    from orjson import loads as orjson_loads

    from cattrs.preconf.orjson import make_converter as orjson_make_converter

    converter = orjson_make_converter(detailed_validation=detailed_validation)
    raw = orjson_dumps(converter.unstructure(everything))
    assert converter.structure(orjson_loads(raw), Everything) == everything


@pytest.mark.skipif(python_implementation() == "PyPy", reason="no orjson on PyPy")
@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    ),
    booleans(),
)
def test_orjson_converter(everything: Everything, detailed_validation: bool):
    from cattrs.preconf.orjson import make_converter as orjson_make_converter

    converter = orjson_make_converter(detailed_validation=detailed_validation)
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_msgpack(everything: Everything):
    from msgpack import dumps as msgpack_dumps
    from msgpack import loads as msgpack_loads

    converter = msgpack_make_converter()
    raw = msgpack_dumps(converter.unstructure(everything))
    assert (
        converter.structure(msgpack_loads(raw, strict_map_key=False), Everything)
        == everything
    )


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_msgpack_converter(everything: Everything):
    converter = msgpack_make_converter()
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything, strict_map_key=False) == everything


@given(
    everythings(
        min_int=-9223372036854775808,
        max_int=9223372036854775807,
        allow_null_bytes_in_keys=False,
        allow_datetime_microseconds=False,
    ),
    booleans(),
)
def test_bson(everything: Everything, detailed_validation: bool):
    from bson import decode as bson_loads
    from bson import encode as bson_dumps

    converter = bson_make_converter(detailed_validation=detailed_validation)
    raw = bson_dumps(
        converter.unstructure(everything), codec_options=CodecOptions(tz_aware=True)
    )
    assert (
        converter.structure(
            bson_loads(raw, codec_options=CodecOptions(tz_aware=True)), Everything
        )
        == everything
    )


@given(
    everythings(
        min_int=-9223372036854775808,
        max_int=9223372036854775807,
        allow_null_bytes_in_keys=False,
        allow_datetime_microseconds=False,
    ),
    booleans(),
)
def test_bson_converter(everything: Everything, detailed_validation: bool):
    converter = bson_make_converter(detailed_validation=detailed_validation)
    raw = converter.dumps(everything, codec_options=CodecOptions(tz_aware=True))
    assert (
        converter.loads(raw, Everything, codec_options=CodecOptions(tz_aware=True))
        == everything
    )


@given(everythings())
def test_pyyaml(everything: Everything):
    from yaml import safe_dump, safe_load

    converter = pyyaml_make_converter()
    unstructured = converter.unstructure(everything)
    raw = safe_dump(unstructured)
    assert converter.structure(safe_load(raw), Everything) == everything


@given(everythings())
def test_pyyaml_converter(everything: Everything):
    converter = pyyaml_make_converter()
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


@given(
    everythings(
        min_key_length=1,
        allow_null_bytes_in_keys=False,
        key_blacklist_characters=['"', "\\"],
        allow_control_characters_in_values=False,
    ),
    booleans(),
)
def test_tomlkit(everything: Everything, detailed_validation: bool):
    from tomlkit import dumps as tomlkit_dumps
    from tomlkit import loads as tomlkit_loads

    converter = tomlkit_make_converter(detailed_validation=detailed_validation)
    unstructured = converter.unstructure(everything)
    raw = tomlkit_dumps(unstructured)
    assert converter.structure(tomlkit_loads(raw), Everything) == everything


@given(
    everythings(
        min_key_length=1,
        allow_null_bytes_in_keys=False,
        key_blacklist_characters=['"', "\\"],
        allow_control_characters_in_values=False,
    ),
    booleans(),
)
def test_tomlkit_converter(everything: Everything, detailed_validation: bool):
    converter = tomlkit_make_converter(detailed_validation=detailed_validation)
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


def test_bson_objectid():
    """BSON ObjectIds are supported by default."""
    converter = bson_make_converter()
    o = ObjectId()
    assert o == converter.structure(str(o), ObjectId)
    assert o == converter.structure(o, ObjectId)
