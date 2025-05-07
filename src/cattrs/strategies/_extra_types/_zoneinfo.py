from functools import cache
from zoneinfo import ZoneInfo

from ...types import StructureHook, UnstructureHook


@cache
def gen_structure_hook(cl: type, _) -> StructureHook | None:
    if issubclass(cl, ZoneInfo):
        return lambda v, _: ZoneInfo(v)
    return None


@cache
def gen_unstructure_hook(cl: type, _) -> UnstructureHook | None:
    if issubclass(cl, ZoneInfo):
        return lambda v: str(v)
    return None
