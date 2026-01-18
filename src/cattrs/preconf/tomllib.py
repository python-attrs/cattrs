"""Preconfigured converters for tomllib."""

from base64 import b85decode, b85encode
from collections.abc import Set
from datetime import date, datetime
from enum import Enum
from operator import attrgetter
from typing import Any, TypeVar, Union

try:
    from tomllib import loads
except ImportError:
    from tomli import loads

try:
    from tomli_w import dumps
except ImportError:  # pragma: nocover
    dumps = None

from .._compat import is_mapping, is_subclass
from ..converters import BaseConverter, Converter
from ..fns import identity
from ..strategies import configure_union_passthrough
from . import validate_datetime, wrap

__all__ = ["TomllibConverter", "configure_converter", "make_converter"]

T = TypeVar("T")
_enum_value_getter = attrgetter("_value_")


class TomllibConverter(Converter):
    """A converter subclass specialized for tomllib."""

    if dumps is not None:

        def dumps(self, obj: Any, unstructure_as: Any = None, **kwargs: Any) -> str:
            return dumps(self.unstructure(obj, unstructure_as=unstructure_as), **kwargs)

    def loads(self, data: str, cl: type[T], **kwargs: Any) -> T:
        return self.structure(loads(data, **kwargs), cl)


def configure_converter(converter: BaseConverter):
    """
    Configure the converter for use with the tomllib library.

    * bytes are serialized as base85 strings
    * sets are serialized as lists
    * tuples are serializas as lists
    * mapping keys are coerced into strings when unstructuring
    * dates and datetimes are left for tomllib to handle
    """
    converter.register_structure_hook(bytes, lambda v, _: b85decode(v))
    converter.register_unstructure_hook(
        bytes, lambda v: (b85encode(v) if v else b"").decode("utf8")
    )

    @converter.register_unstructure_hook_factory(is_mapping)
    def gen_unstructure_mapping(cl: Any, unstructure_to=None):
        key_handler = str
        args = getattr(cl, "__args__", None)
        if args:
            if is_subclass(args[0], str):
                key_handler = _enum_value_getter if is_subclass(args[0], Enum) else None
            elif is_subclass(args[0], bytes):

                def key_handler(k: bytes):
                    return b85encode(k).decode("utf8")

        return converter.gen_unstructure_mapping(
            cl, unstructure_to=unstructure_to, key_handler=key_handler
        )

    converter.register_unstructure_hook(datetime, identity)
    converter.register_structure_hook(datetime, validate_datetime)
    converter.register_unstructure_hook(date, identity)
    converter.register_structure_hook(
        date, lambda v, _: v if isinstance(v, date) else date.fromisoformat(v)
    )
    configure_union_passthrough(Union[str, int, float, bool], converter)


@wrap(TomllibConverter)
def make_converter(*args: Any, **kwargs: Any) -> TomllibConverter:
    kwargs["unstruct_collection_overrides"] = {
        Set: list,
        tuple: list,
        **kwargs.get("unstruct_collection_overrides", {}),
    }
    res = TomllibConverter(*args, **kwargs)
    configure_converter(res)

    return res
