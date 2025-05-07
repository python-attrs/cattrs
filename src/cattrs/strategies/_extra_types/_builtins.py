from collections.abc import Sequence
from functools import cache, partial
from numbers import Real

from ...converters import Converter
from ...preconf import has_format
from ...types import StructureHook, UnstructureHook
from . import raise_unexpected_structure

MISSING_SPECIAL_FLOATS = ("msgspec", "orjson")

SPECIAL = (float("inf"), float("-inf"), float("nan"))
SPECIAL_STR = ("inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan")


@cache
def gen_structure_hook(cl: type, _) -> StructureHook | None:
    if cl is complex:
        return structure_complex
    return None


@cache
def gen_unstructure_hook(cl: type, converter: Converter) -> UnstructureHook | None:
    if cl is complex:
        if has_format(converter, MISSING_SPECIAL_FLOATS):
            return partial(unstructure_complex, special_as_string=True)
        return unstructure_complex
    return None


def structure_complex(obj: object, _) -> complex:
    if (
        isinstance(obj, Sequence)
        and len(obj) == 2
        and all(isinstance(x, (Real, str)) for x in obj)
    ):
        try:
            # for all converters, string inf and nan are allowed
            obj = [
                float(x) if (isinstance(x, str) and x.lower() in SPECIAL_STR) else x
                for x in obj
            ]
            return complex(*obj)
        except ValueError:
            pass  # to error
    raise_unexpected_structure(complex, type(obj))  # noqa: RET503 # NoReturn not handled by Ruff


def unstructure_complex(
    value: complex,
    special_as_string: bool = False,
) -> list[float | str]:
    return [
        str(x) if (x in SPECIAL and special_as_string) else x
        for x in [value.real, value.imag]
    ]
