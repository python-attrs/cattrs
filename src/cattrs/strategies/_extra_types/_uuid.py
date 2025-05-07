from functools import cache
from uuid import UUID

from ...converters import Converter
from ...dispatch import StructureHook, UnstructureHook
from ...fns import identity
from ...preconf import has_format
from . import raise_unexpected_structure

SUPPORTS_UUID = ("bson", "cbor", "msgspec", "orjson")


@cache
def gen_structure_hook(cl: type, _) -> StructureHook | None:
    if issubclass(cl, UUID):
        return structure_uuid
    return None


@cache
def gen_unstructure_hook(cl: type, converter: Converter) -> UnstructureHook | None:
    if issubclass(cl, UUID):
        return identity if has_format(converter, SUPPORTS_UUID) else lambda v: str(v)
    return None


def structure_uuid(value: bytes | int | str, _) -> UUID:
    if isinstance(value, bytes):
        return UUID(bytes=value)
    if isinstance(value, int):
        return UUID(int=value)
    if isinstance(value, str):
        return UUID(value)
    raise_unexpected_structure(UUID, type(value))  # noqa: RET503 # NoReturn
