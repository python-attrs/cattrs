from collections.abc import Callable, Generator, Iterable, Sized
from dataclasses import dataclass
from functools import wraps
from typing import Annotated, Any, Generic, TypeAlias, TypeVar, get_args

from attrs import define, frozen

from cattrs import global_converter
from cattrs._compat import is_annotated
from cattrs.converters import BaseConverter
from cattrs.dispatch import StructureHook
from cattrs.errors import BaseValidationError

T = TypeVar("T")
A = TypeVar("A")
S = TypeVar("S", bound=Sized)

AnyType: TypeAlias = Any
"""Any type (i.e. not an instance). Can be a class, ABC, Protocol, Literal, etc."""

ConstraintPath: TypeAlias = tuple[()] | tuple[str, ...]
"""A path for a constraint check. Empty tuple means the object itself."""

ConstraintHook: TypeAlias = Callable[[T], str | None]
"""A constraint validation check for T. Returns an error string if failed, else None."""


def nonempty_check(val: S) -> str | None:
    return "Collection is empty" if not len(val) else None


@frozen
class Constraint(Generic[T]):
    """Used to create constraint hooks, which can later be called by cattrs.

    Do not instantiate this class directly; use the provided classmethods instead.
    """

    _hook: ConstraintHook[T]
    _target: Any

    @classmethod
    def for_(cls, arg: A) -> "Callable[[ConstraintHook[A]], Constraint[A]]":
        return lambda v: Constraint(v, arg)

    @classmethod
    def nonempty(cls, arg: S) -> "Constraint[S]":
        """Ensure the collection is not empty."""
        return Constraint(nonempty_check, arg)


class ConstraintError(Exception):
    pass


class ConstraintGroupError(BaseValidationError):
    """Raised during detailed validation; may contain multiple constraint violations."""


ValHookFactory = Callable[[T], Iterable[Constraint[T]]]


def _extract_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
    if not is_annotated(type):
        return []
    return [cls for cls in get_args(type)[1:] if isinstance(cls, cls_to_extract)]


def split_from_annotated(type: Any, cls_to_split: type[T]) -> tuple[Any, list[T]]:
    """If the given type is an `Annotated`, extract `cls_to_split` from it.

    Returns:
        The type without `cls_to_split`, and a list of `cls_to_split` instances.
        If there are other `Annotated` members, returns an annotated with them,
        otherwise the bare type.
    """
    if not is_annotated(type):
        return type, []
    args = get_args(type)
    extracted: list[Any] = []
    left: list[Any] = []
    for t in args[1:]:
        (extracted if isinstance(t, cls_to_split) else left).append(t)
    return Annotated[(args[0], *left)] if left else args[0], extracted


@frozen
class Val:
    """For use in `Annotated`, to add val hooks."""

    hooks: tuple[tuple[ConstraintPath, tuple[ConstraintHook[Any], ...]]]


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
    res: dict[ConstraintPath, list[ConstraintHook[Any]]] = {}
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
    val_hook: Callable[[T], Iterable[Constraint[T]]] | None = None,
) -> T:
    if val_hook is not None:
        hooks = _gen_val_hooks(structure_as, val_hook)
        structure_as = Annotated[structure_as, Val(hooks)]  # type: ignore
    return global_converter.structure(obj, structure_as)


@global_converter.register_structure_hook_factory(
    lambda t: bool(_extract_from_annotated(t, Val))
)
def direct_constraint_factory(type: Any, conv: BaseConverter) -> StructureHook:
    base, constraints = split_from_annotated(type, Val)
    instance_constraints = [
        c for con in constraints[0].hooks if con[0] == () for c in con[1]
    ]
    hook = conv.get_structure_hook(base)

    @wraps(hook)
    def check_constraints(val: Any, type: Any) -> Any:
        res = hook(val, type)
        errors: list[Exception] = []
        for con in instance_constraints:
            try:
                if (error := con(res)) is not None:
                    errors.append(ConstraintError(error))
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise ConstraintGroupError("Constraint violations", errors, base)
        return res

    return check_constraints


@define
class B:
    a: int
    b: list[int]


@dataclass
class C:
    c: dict[str, int]


def val(a: B) -> Generator[Constraint[Any]]:
    yield Constraint.for_(a)(lambda b: "b too small" if b.a >= 1 else None)
    yield Constraint.for_(a.a)(lambda a: None if a > 1 else "a too small")
    # yield ValExpr.for_(a.b)(lambda b: len(b) > 0)
