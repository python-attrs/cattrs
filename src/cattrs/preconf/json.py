"""Preconfigured converters for the stdlib json."""

from base64 import b64decode, b64encode, b85decode, b85encode
from collections.abc import Callable, Mapping, Set
from datetime import date, datetime
from json import dumps, loads
from typing import Any, Literal, TypeVar, Union

from typing_extensions import TypeForm

from .._compat import Counter
from ..converters import BaseConverter, Converter, UnstructureStrategy
from ..dispatch import HookFactory, StructureHook, UnstructureHook
from ..fns import identity, raise_error
from ..gen._consts import AttributeOverride
from ..literals import is_literal_containing_enums
from ..strategies import configure_union_passthrough
from . import is_primitive_enum, literals_with_enums_unstructure_factory

__all__ = ["JsonConverter", "configure_converter", "make_converter"]

T = TypeVar("T")


class JsonConverter(Converter):
    def dumps(self, obj: Any, unstructure_as: Any = None, **kwargs: Any) -> str:
        return dumps(self.unstructure(obj, unstructure_as=unstructure_as), **kwargs)

    def loads(self, data: Union[bytes, str], cl: TypeForm[T], **kwargs: Any) -> T:
        """Deserialize and structure the provided data as ``cl``.

        .. versionchanged:: NEXT
            The target type is now annotated with ``TypeForm`` to support
            stronger typing.
        """
        return self.structure(loads(data, **kwargs), cl)


def configure_converter(
    converter: BaseConverter, *, bytes_encoding: Literal["base85", "base64"] = "base85"
) -> None:
    """
    Configure the converter for use with the stdlib json module.

    * bytes are serialized as base85 strings, or base64 if requested
    * datetimes are serialized as ISO 8601
    * counters are serialized as dicts
    * sets are serialized as lists
    * string and int enums are passed through when unstructuring
    * union passthrough is configured for unions of strings, bools, ints,
      floats and None

    .. versionchanged:: 24.2.0
        Enums are left to the library to unstructure, speeding them up.

    .. versionchanged:: NEXT
        *bytes_encoding* selects base85 (the default) or base64 for bytes.
    """
    encode: Callable[[bytes], bytes]
    decode: Callable[[Union[str, bytes]], bytes]
    if bytes_encoding == "base85":
        encode, decode = b85encode, b85decode
    elif bytes_encoding == "base64":
        encode, decode = b64encode, b64decode
    else:
        raise ValueError("bytes_encoding must be 'base85' or 'base64'")
    converter.register_unstructure_hook(bytes, lambda v: encode(v).decode("ascii"))
    converter.register_structure_hook(bytes, lambda v, _: decode(v))
    converter.register_unstructure_hook(datetime, lambda v: v.isoformat())
    converter.register_structure_hook(datetime, lambda v, _: datetime.fromisoformat(v))
    converter.register_unstructure_hook(date, lambda v: v.isoformat())
    converter.register_structure_hook(date, lambda v, _: date.fromisoformat(v))
    converter.register_unstructure_hook_factory(
        is_literal_containing_enums, literals_with_enums_unstructure_factory
    )
    converter.register_unstructure_hook_factory(is_primitive_enum, lambda _: identity)
    configure_union_passthrough(Union[str, bool, int, float, None], converter)


def make_converter(
    dict_factory: Callable[[], Any] = dict,
    unstruct_strat: UnstructureStrategy = UnstructureStrategy.AS_DICT,
    omit_if_default: bool = False,
    forbid_extra_keys: bool = False,
    type_overrides: Mapping[type, AttributeOverride] = {},
    unstruct_collection_overrides: Mapping[type, UnstructureHook] = {},
    prefer_attrib_converters: bool = False,
    detailed_validation: bool = True,
    unstructure_fallback_factory: HookFactory[UnstructureHook] = lambda _: identity,
    structure_fallback_factory: HookFactory[StructureHook] = lambda t: raise_error(
        None, t
    ),
    use_alias: bool = False,
    *,
    bytes_encoding: Literal["base85", "base64"] = "base85",
) -> JsonConverter:
    """Create a JSON converter, optionally using base64 for bytes.

    All other parameters are passed to :class:`cattrs.Converter`.

    .. versionchanged:: NEXT
        *bytes_encoding* selects base85 (the default) or base64 for bytes.
    """
    res = JsonConverter(
        dict_factory=dict_factory,
        unstruct_strat=unstruct_strat,
        omit_if_default=omit_if_default,
        forbid_extra_keys=forbid_extra_keys,
        type_overrides=type_overrides,
        unstruct_collection_overrides={
            Set: list,
            Counter: dict,
            **unstruct_collection_overrides,
        },
        prefer_attrib_converters=prefer_attrib_converters,
        detailed_validation=detailed_validation,
        unstructure_fallback_factory=unstructure_fallback_factory,
        structure_fallback_factory=structure_fallback_factory,
        use_alias=use_alias,
    )
    configure_converter(res, bytes_encoding=bytes_encoding)

    return res
