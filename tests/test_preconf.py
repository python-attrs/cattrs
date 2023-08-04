from datetime import date, datetime, timezone
from enum import Enum, IntEnum, unique
from json import dumps as json_dumps
from json import loads as json_loads
from platform import python_implementation
from typing import Dict, List, Union

import pytest
from attrs import define
from bson import CodecOptions, ObjectId
from hypothesis import given
from hypothesis.strategies import (
    binary,
    booleans,
    characters,
    composite,
    dates,
    datetimes,
    dictionaries,
    floats,
    frozensets,
    integers,
    just,
    lists,
    one_of,
    sets,
    text,
)

from cattrs._compat import (
    AbstractSet,
    Counter,
    FrozenSet,
    FrozenSetSubscriptable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
    TupleSubscriptable,
)
from cattrs.preconf.bson import make_converter as bson_make_converter
from cattrs.preconf.cbor2 import make_converter as cbor2_make_converter
from cattrs.preconf.json import make_converter as json_make_converter
from cattrs.preconf.msgpack import make_converter as msgpack_make_converter
from cattrs.preconf.pyyaml import make_converter as pyyaml_make_converter
from cattrs.preconf.tomlkit import make_converter as tomlkit_make_converter
from cattrs.preconf.ujson import make_converter as ujson_make_converter


@define
class A:
    a: int


@define
class B:
    b: str


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
    a_date: date
    a_string_enum_dict: Dict[AStringEnum, int]
    a_bytes_dict: Dict[bytes, bytes]
    native_union: Union[int, float, str]
    native_union_with_spillover: Union[int, str, set[str]]
    native_union_with_union_spillover: Union[int, str, A, B]


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
    fs = floats(allow_nan=False, allow_infinity=allow_inf)
    ints = integers(min_value=min_int, max_value=max_int)

    return Everything(
        draw(strings),
        draw(binary()),
        draw(ints),
        draw(fs),
        draw(dictionaries(key_text, ints)),
        draw(lists(ints)),
        tuple(draw(lists(ints))),
        (draw(strings), draw(ints), draw(fs)),
        Counter(draw(dictionaries(key_text, ints))),
        draw(dictionaries(ints, fs)),
        draw(dictionaries(fs, strings)),
        draw(lists(fs)),
        draw(lists(strings)),
        draw(sets(fs)),
        draw(sets(ints)),
        draw(frozensets(strings)),
        Everything.AnIntEnum.A,
        Everything.AStringEnum.A,
        draw(dts),
        draw(dates(min_value=date(1970, 1, 1), max_value=date(2038, 1, 1))),
        draw(
            dictionaries(
                just(Everything.AStringEnum.A),
                integers(min_value=min_int, max_value=max_int),
            )
        ),
        draw(dictionaries(just(Everything.AStringEnum.A), ints)),
        draw(dictionaries(binary(min_size=min_key_length), binary())),
        draw(one_of(ints, fs, strings)),
        draw(one_of(ints, strings, sets(strings))),
        draw(one_of(ints, strings, ints.map(A), strings.map(B))),
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


@given(everythings())
def test_stdlib_json_converter_unstruct_collection_overrides(everything: Everything):
    converter = json_make_converter(unstruct_collection_overrides={AbstractSet: sorted})
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    )
)
def test_ujson_converter_unstruct_collection_overrides(everything: Everything):
    converter = ujson_make_converter(
        unstruct_collection_overrides={AbstractSet: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@pytest.mark.skipif(python_implementation() == "PyPy", reason="no orjson on PyPy")
@given(
    everythings(
        min_int=-9223372036854775808, max_int=9223372036854775807, allow_inf=False
    )
)
def test_orjson_converter_unstruct_collection_overrides(everything: Everything):
    from cattrs.preconf.orjson import make_converter as orjson_make_converter

    converter = orjson_make_converter(
        unstruct_collection_overrides={AbstractSet: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_msgpack_converter_unstruct_collection_overrides(everything: Everything):
    converter = msgpack_make_converter(
        unstruct_collection_overrides={AbstractSet: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@given(
    everythings(
        min_int=-9223372036854775808,
        max_int=9223372036854775807,
        allow_null_bytes_in_keys=False,
        allow_datetime_microseconds=False,
    )
)
def test_bson_converter_unstruct_collection_overrides(everything: Everything):
    converter = bson_make_converter(unstruct_collection_overrides={AbstractSet: sorted})
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@given(everythings())
def test_pyyaml_converter_unstruct_collection_overrides(everything: Everything):
    converter = pyyaml_make_converter(
        unstruct_collection_overrides={FrozenSetSubscriptable: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


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


@given(
    everythings(
        min_key_length=1,
        allow_null_bytes_in_keys=False,
        key_blacklist_characters=['"', "\\"],
        allow_control_characters_in_values=False,
    )
)
def test_tomlkit_converter_unstruct_collection_overrides(everything: Everything):
    converter = tomlkit_make_converter(
        unstruct_collection_overrides={AbstractSet: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


def test_bson_objectid():
    """BSON ObjectIds are supported by default."""
    converter = bson_make_converter()
    o = ObjectId()
    assert o == converter.structure(str(o), ObjectId)
    assert o == converter.structure(o, ObjectId)


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_cbor2(everything: Everything):
    from cbor2 import dumps as cbor2_dumps
    from cbor2 import loads as cbor2_loads

    converter = cbor2_make_converter()
    raw = cbor2_dumps(converter.unstructure(everything))
    assert converter.structure(cbor2_loads(raw), Everything) == everything


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_cbor2_converter(everything: Everything):
    converter = cbor2_make_converter()
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


@given(everythings(min_int=-9223372036854775808, max_int=18446744073709551615))
def test_cbor2_converter_unstruct_collection_overrides(everything: Everything):
    converter = cbor2_make_converter(
        unstruct_collection_overrides={AbstractSet: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_set"] == sorted(raw["a_set"])
    assert raw["a_mutable_set"] == sorted(raw["a_mutable_set"])
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])
