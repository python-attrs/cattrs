from collections.abc import Callable, Collection, Generator, Iterable
from dataclasses import dataclass
from typing import Annotated, Any, Generic, TypeVar, get_args

from attrs import define, frozen

from cattrs import global_converter
from cattrs._compat import is_annotated

T = TypeVar("T")
A = TypeVar("A")


@frozen
class ValExpr(Generic[T]):
    _hook: Callable[[T], bool]
    _target: Any

    @classmethod
    def for_(cls, arg: A) -> "Callable[[Callable[[A], bool]], ValExpr[A]]":
        return lambda v: ValExpr(v, target=arg)

    @classmethod
    def for_each(
        cls, arg: Iterable[A]
    ) -> "Callable[[Callable[[A], bool]], ValExpr[A]]":
        return lambda v: ValExpr(v, target=arg)

    @classmethod
    def nonempty(cls, arg: Collection[A]) -> "ValExpr[A]":
        return ValExpr(bool, target=arg)


ValHookFactory = Callable[[T], Iterable[ValExpr[T]]]


@define
class B:
    a: int
    b: list[int]


@dataclass
class C:
    c: dict[str, int]


def val(a: B) -> Generator[ValExpr[Any]]:
    yield ValExpr.for_(a.a)(lambda a: a > 1)
    yield ValExpr.for_(a.b)(lambda b: len(b) > 0)


def _extract_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
    if not is_annotated(type):
        return []
    return [cls for cls in get_args(type)[1:] if isinstance(cls, cls_to_extract)]


@frozen
class Val:
    """For use in `Annotated`, to add val hooks."""

    hooks: tuple[Any]


@frozen(slots=False, init=False)
class _ValDummy:
    """A validation dummy, used to gather the validation hooks."""

    def __init__(self, path: tuple[str, ...]) -> None:
        # We use a dotted name in `__dict__` to avoid clashes in `getattr`
        self.__dict__[".path"] = path

    def __getattr__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))


def _gen_val_hooks(type: Any, val_hook_factory: ValHookFactory[Any]) -> tuple[Any, ...]:
    """Generate a mapping of attributes to their validation hooks.

    An empty string means the root object itself.
    """
    res: dict[tuple[str, ...], list[Callable[[Any], bool]]] = {}
    exprs = list(val_hook_factory(_ValDummy(())))

    for expr in exprs:
        target = expr._target
        path = target.__dict__[".path"]
        if not path:
            res.setdefault((), []).append(expr._hook)
        else:
            res.setdefault(tuple(path), []).append(expr._hook)
    return tuple((k, tuple(v)) for k, v in res.items())


def structure(
    obj: Any,
    structure_as: type[T],
    val_hook: Callable[[T], Iterable[ValExpr[object]]] | None = None,
) -> T:
    if val_hook is not None:
        hooks = _gen_val_hooks(structure_as, val_hook)
        print(hooks)
        structure_as = Annotated[structure_as, Val(hooks)]  # type: ignore
    return global_converter.structure(obj, structure_as)


structure({"a": 1, "b": []}, B, val)

# structure({}, B, lambda a: [ValExpr.for_(a.a)(lambda a: a > 1)])

# structure(
#     [],
#     list[int],
#     lambda lst: [
#         ValExpr.for_(lst)(lambda lst: bool(lst)),
#         ValExpr.nonempty(lst),
#         ValExpr.for_each(lst)(lambda e: e > 0),
#     ],
# )
