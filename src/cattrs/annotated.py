"""Utilities for dealing with `typing.Annotated."""

from typing import Annotated, Any, TypeVar, get_args

from ._compat import is_annotated

T = TypeVar("T")

__all__ = ["get_from_annotated", "is_annotated"]


def get_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
    if not is_annotated(type):
        return []
    return [cls for cls in get_args(type)[1:] if isinstance(cls, cls_to_extract)]


def add_to_annotated(type: Any, annotation: Any) -> Any:
    """Add an `Annotated` annotation to an `Annotated` type.

    If the type is not already `Annotated`, make it so.

    .. versionadded:: NEXT
    """
    if not is_annotated(type):
        return Annotated[type, annotation]
    return Annotated[(*get_args(type), annotation)]
