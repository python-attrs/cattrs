"""Utilities for dealing with `typing.Annotated."""

from typing import Annotated, Any, TypeVar, get_args

from ._compat import is_annotated

T = TypeVar("T")

__all__ = ["add_to_annotated", "get_from_annotated", "is_annotated", "split_from_annotated"]


def get_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
    if not is_annotated(type):
        return []
    return [cls for cls in get_args(type)[1:] if isinstance(cls, cls_to_extract)]


def split_from_annotated(type: Any, cls_to_split: type[T]) -> tuple[Any, list[T]]:
    """If the given type is an `Annotated`, extract `cls_to_split` from it.

    Returns:
        The type without `cls_to_split`, and a list of `cls_to_split` instances.
        If there are other `Annotated` members, returns an annotated with them,
        otherwise the bare type.
    """
    if not is_annotated(type):
        return type, []
    args = get_args(type)
    extracted: list[Any] = []
    left: list[Any] = []
    for t in args[1:]:
        (extracted if isinstance(t, cls_to_split) else left).append(t)
    return Annotated[(args[0], *left)] if left else args[0], extracted


def add_to_annotated(type: Any, annotation: Any) -> Any:
    """Add an `Annotated` annotation to an `Annotated` type.

    If the type is not already `Annotated`, make it so.

    .. versionadded:: NEXT
    """
    if not is_annotated(type):
        return Annotated[type, annotation]
    return Annotated[(*get_args(type), annotation)]
