"""Preconfigured converters for bson."""
from datetime import datetime
from typing import Any, Type, TypeVar

from bson import DEFAULT_CODEC_OPTIONS, CodecOptions, ObjectId, decode, encode

from cattrs._compat import Set, is_mapping

from ..converters import GenConverter
from . import validate_datetime

T = TypeVar("T")


class BsonConverter(GenConverter):
    def dumps(
        self,
        obj: Any,
        unstructure_as=None,
        check_keys: bool = False,
        codec_options: CodecOptions = DEFAULT_CODEC_OPTIONS,
    ) -> bytes:
        return encode(
            self.unstructure(obj, unstructure_as=unstructure_as),
            check_keys=check_keys,
            codec_options=codec_options,
        )

    def loads(
        self,
        data: bytes,
        cl: Type[T],
        codec_options: CodecOptions = DEFAULT_CODEC_OPTIONS,
    ) -> T:
        return self.structure(decode(data, codec_options=codec_options), cl)


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the bson library.

    * sets are serialized as lists
    * non-string mapping keys are coerced into strings when unstructuring
    * a deserialization hook is registered for bson.ObjectId by default
    """

    def gen_unstructure_mapping(cl: Any, unstructure_to=None):
        key_handler = str
        args = getattr(cl, "__args__", None)
        if args and issubclass(args[0], str):
            key_handler = None
        return converter.gen_unstructure_mapping(
            cl, unstructure_to=unstructure_to, key_handler=key_handler
        )

    converter._unstructure_func.register_func_list(
        [(is_mapping, gen_unstructure_mapping, True)]
    )

    converter.register_structure_hook(datetime, validate_datetime)
    converter.register_structure_hook(ObjectId, lambda v, _: ObjectId(v))


def make_converter(*args, **kwargs) -> BsonConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
    }
    res = BsonConverter(*args, **kwargs)
    configure_converter(res)

    return res
