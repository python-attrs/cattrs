from collections.abc import Callable, Collection, Iterable, Sequence
from typing import Any, assert_never

from attrs import define
from pg import Constraint, structure


@define
class A:
    a: int
    b: list[int]


Constraint.for_(1, lambda a: "failed" if a < 0 else None)

structure(
    {}, int, lambda a: [Constraint.for_(1, lambda a: "failed" if a < 0 else None)]
)


def f[T](a: Callable[[T], Iterable[list[T]]]) -> None: ...


f(lambda a: [assert_never(True)])
