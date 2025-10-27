from collections.abc import Callable, Collection, Generator, Iterable
from dataclasses import dataclass
from typing import Any

from attrs import Factory, define, frozen

from cattrs import global_converter


@define
class A:
    a: int
    b: list[int]


@dataclass
class B:
    c: dict[str, int]


@frozen
class ValExpr[T]:
    _hook: Callable[[T], bool]
    _target: Any

    @classmethod
    def for_(cls, arg: T) -> "Callable[[Callable[[T], bool]], ValExpr]":
        return lambda v: ValExpr(v, _target=arg)

    @classmethod
    def for_each(cls, arg: Iterable[T]) -> "Callable[[Callable[[T], bool]], ValExpr]":
        return lambda v: ValExpr(v)

    @classmethod
    def nonempty(cls, arg: Collection[T]) -> "ValExpr":
        return ValExpr(bool)


type ValHookFactory[T] = Callable[[T], Iterable[ValExpr]]


def val(a: A) -> Generator[ValExpr]:
    yield ValExpr.for_(a.a)(lambda a: a > 1)
    yield ValExpr.for_(a.b)(lambda b: len(b) > 0)


@frozen
class ValDummy:
    """A validation dummy, used to gather the validation hooks."""

    path: list[str] = Factory(list)

    def __getattribute__(self, name):
        return ValDummy(path=[*self.path, name])


def _gen_val_hooks(type, val_hook_factory: ValHookFactory) -> dict[str, Any]:
    """Generate a mapping of attributes to their validation hooks.

    An empty string means the root object itself.
    """
    res = {}
    exprs = list(val_hook_factory(ValDummy()))

    for expr in exprs:
        target_path = expr._target_path
        if not target_path:
            res.setdefault("", []).append(expr)
    return res


def structure[T](
    obj: Any,
    structure_as: type[T],
    val_hook: Callable[[T], Iterable[ValExpr]] | None = None,
) -> T:
    if val_hook is not None:
        hooks = _gen_val_hooks(structure_as, val_hook)
        print(hooks)
    return global_converter.structure(obj, structure_as)


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
