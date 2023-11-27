from __future__ import annotations

from collections.abc import Hashable, Iterable
from typing import Callable, Collection, Protocol, Sized, TypeVar

from .._compat import ExceptionGroup
from ..errors import IterableValidationError, IterableValidationNote
from ._fluent import ValidatorFactory

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


def ignoring_none(
    validator: Callable[[T], None], *validators: Callable[[T], None]
) -> ValidatorFactory[T | None]:
    """
    Wrap validators with this so they can be applied to types that include `None`.

    Values that are equal to `None` are passed through.
    """

    validators = (validator, *validators)

    def factory(detailed_validation: bool) -> Callable[[T | None], None]:
        if detailed_validation:

            def skip_none(val: T | None, _validators=validators) -> None:
                if val is None:
                    return
                errors = []
                for validator in _validators:
                    try:
                        validator(val)
                    except Exception as exc:
                        errors.append(exc)
                if errors:
                    raise ExceptionGroup("", errors)

        else:

            def skip_none(val: T | None, _validators=validators) -> None:
                if val is None:
                    return
                for validator in _validators:
                    validator(val)

        return skip_none

    return factory


def all_elements_must(
    validator: Callable[[T], None | bool], *validators: Callable[[T], None | bool]
) -> ValidatorFactory[T]:
    """A helper validator included with cattrs.

    Run all the given validators against all members of the
    iterable.
    """

    validators = (validator, *validators)

    def factory(detailed_validation: bool) -> Callable[[T], None]:
        if detailed_validation:

            def assert_all_elements(val: Iterable[T], _validators=validators) -> None:
                errors = []
                ix = 0
                for e in val:
                    try:
                        for v in _validators:
                            try:
                                v(e)
                            except Exception as exc:
                                exc.__notes__ = [
                                    *getattr(exc, "__notes__", []),
                                    IterableValidationNote(
                                        f"Validating @ index {ix}", ix, None
                                    ),
                                ]
                                errors.append(exc)
                    finally:
                        ix += 1
                if errors:
                    raise IterableValidationError("", errors, val.__class__)

        else:

            def assert_all_elements(val: Iterable[T], _validators=validators) -> None:
                for e in val:
                    for v in _validators:
                        v(e)

        return assert_all_elements

    return factory
