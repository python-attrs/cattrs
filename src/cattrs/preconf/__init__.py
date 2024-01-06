from datetime import datetime
from typing import Any, Callable, ParamSpec, TypeVar


def validate_datetime(v, _):
    if not isinstance(v, datetime):
        raise Exception(f"Expected datetime, got {v}")
    return v


T = TypeVar("T")
P = ParamSpec("P")


def wrap(inner: Callable[P, Any]) -> Callable[[Callable[..., T]], Callable[P, T]]:
    """Wrap a `Converter` `__init__` in a type-safe way."""

    def impl(x: Callable[..., T]) -> Callable[P, T]:
        return inner

    return impl
