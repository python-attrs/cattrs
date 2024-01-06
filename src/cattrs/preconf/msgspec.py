"""Preconfigured converters for msgspec."""
from __future__ import annotations

from base64 import b64decode
from datetime import date, datetime
from typing import Any, Callable, ParamSpec, TypeVar, Union

from msgspec.json import decode, encode

from ..converters import BaseConverter, Converter
from ..strategies import configure_union_passthrough

T = TypeVar("T")
P = ParamSpec("P")


def wrap(inner: Callable[P, Any]) -> Callable[[Callable[..., T]], Callable[P, T]]:
    def impl(x: Callable[..., T]) -> Callable[P, T]:
        return inner

    return impl


class MsgspecJsonConverter(Converter):
    def dumps(self, obj: Any, unstructure_as: Any = None, **kwargs: Any) -> bytes:
        return encode(self.unstructure(obj, unstructure_as=unstructure_as), **kwargs)

    def loads(self, data: bytes, cl: type[T], **kwargs: Any) -> T:
        return self.structure(decode(data, **kwargs), cl)


def configure_converter(converter: BaseConverter) -> None:
    """Configure the converter for the msgspec library.

    * bytes are serialized as base64 strings, directly by msgspec
    * datetimes and dates are passed through to be serialized as RFC 3339 directly
    * union passthrough configured for str, bool, int, float and None
    """
    converter.register_structure_hook(bytes, lambda v, _: b64decode(v))
    converter.register_structure_hook(datetime, lambda v, _: datetime.fromisoformat(v))
    converter.register_structure_hook(date, lambda v, _: date.fromisoformat(v))
    configure_union_passthrough(Union[str, bool, int, float, None], converter)


@wrap(MsgspecJsonConverter)
def make_converter(*args: Any, **kwargs: Any) -> MsgspecJsonConverter:
    res = MsgspecJsonConverter(*args, **kwargs)
    configure_converter(res)
    return res
