"""The cattrs constraint system."""

from collections.abc import Callable
from typing import Any, TypeAlias, TypeVar

from attrs import frozen

T = TypeVar("T")

ConstraintHook: TypeAlias = Callable[[T], str | None]
"""A constraint validation check for T. Returns an error string if failed, else None."""


ConstraintPath: TypeAlias = tuple[()] | tuple[str, ...]
"""
A path for a constraint check.

* Empty tuple means the object itself.
* A string means an attribute.

"""

type frozenlist[T] = tuple[T, ...]


@frozen
class ConstraintAnnotated:
    """For use in `Annotated`, to add constraint hooks."""

    hooks: frozenlist[tuple[ConstraintPath, frozenlist[ConstraintHook[Any]]]]
