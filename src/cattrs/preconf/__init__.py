from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ParamSpec, TypeVar, get_args

from .._compat import is_subclass
from ..converters import Converter, UnstructureHook
from ..errors import CattrsError
from ..fns import identity


def validate_datetime(v, _):
    if not isinstance(v, datetime):
        raise CattrsError(f"Expected datetime, got {v}")
    return v


def unstructure_datetime_as_timestamp(v: datetime) -> float:
    """Unstructure a datetime into a UNIX timestamp.

    `datetime.timestamp` interprets naive datetimes as local time, which would
    make the result depend on the timezone of the machine unstructuring them.
    The matching structure hooks read timestamps back as UTC, so naive
    datetimes are treated as UTC here too, keeping both ends of the round-trip
    in agreement.
    """
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    return v.timestamp()


T = TypeVar("T")
P = ParamSpec("P")


def wrap(_: Callable[P, Any]) -> Callable[[Callable[..., T]], Callable[P, T]]:
    """Wrap a `Converter` `__init__` in a type-safe way."""

    def impl(x: Callable[..., T]) -> Callable[P, T]:
        return x

    return impl


def is_primitive_enum(type: Any, include_bare_enums: bool = False) -> bool:
    """Is this a string or int enum that can be passed through?"""
    return is_subclass(type, Enum) and (
        is_subclass(type, (str, int))
        or (include_bare_enums and type.mro()[1:] == Enum.mro())
    )


def literals_with_enums_unstructure_factory(
    typ: Any, converter: Converter
) -> UnstructureHook:
    """An unstructure hook factory for literals containing enums.

    If all contained enums can be passed through (their unstructure hook is `identity`),
    the entire literal can also be passed through.
    """
    if all(
        converter.get_unstructure_hook(type(arg)) == identity for arg in get_args(typ)
    ):
        return identity
    return converter.unstructure
