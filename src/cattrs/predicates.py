"""Useful predicates."""

from typing import Any, get_args

from ._compat import has_with_generic
from .annotated import is_annotated


def is_attrs_or_dataclass(type: Any) -> bool:
    """
    A predicate function for both attrs and dataclasses.

    Work with generic classes, and with `Annotated`.
    """
    return has_with_generic(type if not is_annotated(type) else get_args(type)[0])
