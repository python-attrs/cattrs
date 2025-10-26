from collections.abc import Callable, Collection, Generator, Iterable
from dataclasses import dataclass
from typing import Any

from attrs import define, frozen


@define
class A:
    a: int
    b: list[int]


@dataclass
class B:
    c: dict[str, int]


@frozen
class ValExpr[T]:
    b: Callable[[T], bool]

    @classmethod
    def for_(cls, arg: T) -> "Callable[[Callable[[T], bool]], ValExpr]":
        return lambda v: ValExpr(v)

    @classmethod
    def for_each(cls, arg: Iterable[T]) -> "Callable[[Callable[[T], bool]], ValExpr]":
        return lambda v: ValExpr(v)

    @classmethod
    def nonempty(cls, arg: Collection[T]) -> "ValExpr":
        return ValExpr(bool)


def val(a: A) -> Generator[ValExpr]:
    yield ValExpr.for_(a.a)(lambda a: a > 1)
    yield ValExpr.for_(a.b)(lambda b: len(b) > 0)


reveal_type(val)


def structure[T](
    obj: Any,
    structure_as: type[T],
    val_hook: Callable[[T], Iterable[ValExpr]] | None = None,
) -> T:
    return None  # type: ignore


structure({}, A, val)

structure({}, A, lambda a: [ValExpr.for_(a.a)(lambda a: a > 1)])

structure(
    [],
    list[int],
    lambda lst: [
        ValExpr.for_(lst)(lambda lst: bool(lst)),
        ValExpr.nonempty(lst),
        ValExpr.for_each(lst)(lambda e: e > 0),
    ],
)
