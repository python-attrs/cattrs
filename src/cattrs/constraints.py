"""The cattrs constraint system."""

from collections.abc import Callable, Iterable, Mapping, Sized
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
    VALUES = "values"
    """Apply a constraint to each value of a mapping."""
    ITEMS = "items"
    """Apply a constraint to each item (key, value) of a mapping."""


ConstraintPath: TypeAlias = tuple[()] | tuple[str | ConstraintPathSentinel, ...]
"""
A path for a constraint check.

* Empty tuple means the object itself.
* A string means an attribute.

"""

frozenlist: TypeAlias = tuple[T, ...]


@frozen
class ConstraintAnnotated:
    """For use in `Annotated`, to add constraint hooks."""

    hooks: frozenlist[tuple[ConstraintPath, frozenlist[ConstraintHook[Any]]]]


def nonempty_check(val: S) -> str | None:
    return "Collection is empty" if not len(val) else None


@frozen
class Constraint(Generic[T]):
    """Used to create constraint hooks, which can later be called by cattrs.

    See the `for_`, `each`, `values` and `items` classmethods for handling composite
    types.
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
        """Ensure the hook passes for each element of an iterable.

        Using iteration directly should usually be preferred:

            [Constraint(hook, e) for e in my_object]

        which is equivalent to:

            Constraint.each(my_object, hook)
        """
        return Constraint(hook, iterable, ConstraintPathSentinel.EACH)

    @classmethod
    def values(
        cls, mapping: Mapping[Any, A], hook: ConstraintHook[A]
    ) -> "Constraint[Mapping[Any, A]]":
        """Ensure the hook passes for each value of a mapping."""
        return Constraint(hook, mapping, ConstraintPathSentinel.VALUES)

    @classmethod
    def items(
        cls, mapping: Mapping[A, T], hook: ConstraintHook[tuple[A, T]]
    ) -> "Constraint[Mapping[A, T]]":
        """Ensure the hook passes for each item (key, value) of a mapping."""
        return Constraint(hook, mapping, ConstraintPathSentinel.ITEMS)
