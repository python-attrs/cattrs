from collections.abc import Sequence
from typing import Literal, TypeAlias, TYPE_CHECKING, TypeIs, Union, get_args, overload

from ..converters import Converter
from ..types import Unavailable

if TYPE_CHECKING:
    try:
        from cattrs.preconf.bson import BsonConverter
    except ModuleNotFoundError:
        BsonConverter = Unavailable

    try:
        from cattrs.preconf.cbor2 import Cbor2Converter
    except ModuleNotFoundError:
        Cbor2Converter = Unavailable
    
    from cattrs.preconf.json import JsonConverter
    
    try:
        from cattrs.preconf.msgpack import MsgpackConverter
    except ModuleNotFoundError:
        MsgpackConverter = Unavailable
    
    try:
        from cattrs.preconf.msgspec import MsgspecJsonConverter
    except ModuleNotFoundError:
        MsgspecJsonConverter = Unavailable
    
    try:
        from cattrs.preconf.orjson import OrjsonConverter
    except ModuleNotFoundError:
        OrjsonConverter = Unavailable
    
    try:
        from cattrs.preconf.pyyaml import PyyamlConverter
    except ModuleNotFoundError:
        PyyamlConverter = Unavailable
    
    try:
        from cattrs.preconf.tomlkit import TomlkitConverter
    except ModuleNotFoundError:
        TomlkitConverter = Unavailable
    
    try:
        from cattrs.preconf.ujson import UjsonConverter
    except ModuleNotFoundError:
        UjsonConverter = Unavailable

    PreconfiguredConverter: TypeAlias = Union[
        BsonConverter,
        Cbor2Converter,
        JsonConverter,
        MsgpackConverter,
        MsgspecJsonConverter,
        OrjsonConverter,
        PyyamlConverter,
        TomlkitConverter,
        UjsonConverter,
    ]

else:
    PreconfiguredConverter: TypeAlias = Converter

ConverterFormat: TypeAlias = Literal[
    "bson", "cbor2", "json", "msgpack", "msgspec", "orjson", "pyyaml", "tomlkit",
    "ujson",
]

C: TypeAlias = Converter | Unavailable


@overload
def has_type(converter: C, fmt: Literal["bson"]) -> TypeIs["BsonConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["cbor2"]) -> TypeIs["Cbor2Converter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["json"]) -> TypeIs["JsonConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["msgpack"]) -> TypeIs["MsgpackConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["msgspec"]) -> TypeIs["MsgspecJsonConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["orjson"]) -> TypeIs["OrjsonConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["pyyaml"]) -> TypeIs["PyyamlConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["tomlkit"]) -> TypeIs["TomlkitConverter"]:
    ...
@overload
def has_type(converter: C, fmt: Literal["ujson"]) -> TypeIs["UjsonConverter"]:
    ...
def has_type(converter: C, fmt: ConverterFormat | str | Sequence[ConverterFormat]) -> bool:
    if isinstance(fmt, str):
        fmt = (fmt,)

    if "bson" in fmt and converter.__class__.__name__ == "BsonConverter":
        from .bson import BsonConverter

        return isinstance(converter, BsonConverter)

    if "cbor2" in fmt  and converter.__class__.__name__ == "Cbor2Converter":
        from .cbor2 import Cbor2Converter

        return isinstance(converter, Cbor2Converter)

    if "json" in fmt  and converter.__class__.__name__ == "JsonConverter":
        from .json import JsonConverter

        return isinstance(converter, JsonConverter)

    if "msgpack" in fmt  and converter.__class__.__name__ == "MsgpackConverter":
        from .msgpack import MsgpackConverter

        return isinstance(converter, MsgpackConverter)

    if "msgspec" in fmt  and converter.__class__.__name__ == "MsgspecJsonConverter":
        from .msgspec import MsgspecJsonConverter

        return isinstance(converter, MsgspecJsonConverter)

    if "orjson" in fmt  and converter.__class__.__name__ == "OrjsonConverter":
        from .orjson import OrjsonConverter

        return isinstance(converter, OrjsonConverter)

    if "pyyaml" in fmt  and converter.__class__.__name__ == "PyyamlConverter":
        from .pyyaml import PyyamlConverter

        return isinstance(converter, PyyamlConverter)

    if "tomlkit" in fmt  and converter.__class__.__name__ == "TomlkitConverter":
        from .tomlkit import TomlkitConverter

        return isinstance(converter, TomlkitConverter)

    if "ujson" in fmt  and converter.__class__.__name__ == "UjsonConverter":
        from .ujson import UjsonConverter

        return isinstance(converter, UjsonConverter)

    return False


def  is_preconfigured(converter: Converter) -> bool:
    return any(has_type(converter, fmt) for fmt in get_args(ConverterFormat))
