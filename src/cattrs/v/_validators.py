from __future__ import annotations

from collections.abc import Hashable
from typing import Callable, Collection, Protocol, Sized, TypeVar

T = TypeVar("T")


class Comparable(Protocol[T]):
    def __lt__(self: T, other: T) -> bool:
        ...

    def __eq__(self: T, other: T) -> bool:
        ...


C = TypeVar("C", bound=Comparable)


def greater_than(min: C) -> Callable[[C], None]:
    def assert_gt(val: C, _min: C = min) -> None:
        if _min >= val:
            raise ValueError(f"{val} not greater than {_min}")

    return assert_gt


def between(min: C, max: C) -> Callable[[C], None]:
    """Ensure the value of the attribute is between min (inclusive) and max (exclusive)."""

    def assert_between(val: C, _min: C = min, _max: C = max) -> None:
        if val < _min or val >= _max:
            raise ValueError(f"{val} not between {_min} and {_max}")

    return assert_between


def len_between(min: int, max: int) -> Callable[[Sized], None]:
    """Ensure the length of the argument is between min (inclusive) and max (exclusive)."""

    def assert_len_between(val: Sized, _min: int = min, _max: int = max) -> None:
        length = len(val)
        if not (_min <= length < _max):
            raise ValueError(f"length ({length}) not between {_min} and {_max}")

    return assert_len_between


def is_unique(val: Collection[Hashable]) -> None:
    """Ensure all elements in a collection are unique."""
    if (length := len(val)) != (unique_length := len(set(val))):
        raise ValueError(
            f"Collection ({length} elem(s)) not unique, only {unique_length} unique elem(s)"
        )
