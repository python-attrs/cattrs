"""Utilities for dealing with `typing.Annotated."""

from typing import Any, TypeVar, get_args

from ._compat import is_annotated

T = TypeVar("T")


def get_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
    if not is_annotated(type):
        return []
    return [cls for cls in get_args(type)[1:] if isinstance(cls, cls_to_extract)]
