"""The cattrs constraint system."""

from collections.abc import Callable, Iterable, Sized
from enum import Enum
from typing import Any, Generic, TypeAlias, TypeVar

from attrs import frozen

T = TypeVar("T")
A = TypeVar("A")
S = TypeVar("S", bound=Sized)

ConstraintHook: TypeAlias = Callable[[T], str | None]
"""A constraint validation check for T. Returns an error string if failed, else None."""


class ConstraintPathSentinel(Enum):
    """Sentinels for special constraint paths."""

    EACH = "each"
    """Apply a constraint to each element of an iterable."""


ConstraintPath: TypeAlias = tuple[()] | tuple[str | ConstraintPathSentinel, ...]
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


def nonempty_check(val: S) -> str | None:
    return "Collection is empty" if not len(val) else None


@frozen
class Constraint(Generic[T]):
    """Used to create constraint hooks, which can later be called by cattrs.

    Do not instantiate this class directly; use the provided classmethods instead.
    """

    _hook: ConstraintHook[T]
    _target: Any
    _op: ConstraintPathSentinel | None = None

    @classmethod
    def for_(cls, arg: A, hook: ConstraintHook[A]) -> "Constraint[A]":
        return Constraint(hook, arg)

    @classmethod
    def nonempty(cls, arg: S) -> "Constraint[S]":
        """Ensure the collection is not empty."""
        return Constraint(nonempty_check, arg)

    @classmethod
    def each(
        cls, iterable: Iterable[A], hook: ConstraintHook[A]
    ) -> "Constraint[Iterable[A]]":
        """Ensure the hook passes for each element of an iterable."""
        return Constraint(hook, iterable, ConstraintPathSentinel.EACH)
