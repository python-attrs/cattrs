from collections.abc import Callable, Iterable, Sized
from functools import wraps
from typing import Annotated, Any, Generic, TypeAlias, TypeVar, get_args

from attrs import frozen

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
    def for_(cls, arg: A, hook: ConstraintHook[A]) -> "Constraint[A]":
        return Constraint(hook, arg)

    @classmethod
    def nonempty(cls, arg: S) -> "Constraint[S]":
        """Ensure the collection is not empty."""
        return Constraint(nonempty_check, arg)


class ConstraintError(Exception):
    pass


class ConstraintGroupError(BaseValidationError):
    """Raised during detailed validation; may contain multiple constraint violations."""


ConstraintHookFactory = Callable[[T], Iterable[Constraint[T]]]


def _get_from_annotated(type: Any, cls_to_extract: type[T]) -> list[T]:
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

    hooks: frozenlist[tuple[ConstraintPath, tuple[ConstraintHook[Any], ...]]]


@frozen(slots=False, init=False)
class _ValDummy:
    """A validation dummy, used to gather the validation hooks."""

    def __init__(self, path: tuple[str, ...]) -> None:
        # We use a dotted name in `__dict__` to avoid clashes in `getattr`
        self.__dict__[".path"] = path

    def __getattr__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))


def _gen_constraint_hooks(
    type: Any, val_hook_factory: ConstraintHookFactory[Any]
) -> tuple[Any, ...]:
    """Generate a mapping of attributes to their constraint hooks.

    An empty tuple means the root object itself.
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
    if val_hook:
        hooks = _gen_constraint_hooks(structure_as, val_hook)
        structure_as = Annotated[structure_as, ConstraintAnnotated(hooks)]  # type: ignore
    return global_converter.structure(obj, structure_as)


@global_converter.register_structure_hook_factory(
    lambda t: any(
        hook[0] == ()
        for annotated in _get_from_annotated(t, ConstraintAnnotated)
        for hook in annotated.hooks
    )
)
def direct_constraint_factory(type: Any, conv: BaseConverter) -> StructureHook:
    base, constraints = split_from_annotated(type, ConstraintAnnotated)
    instance_constraint_hooks = [
        c for con in constraints[0].hooks if con[0] == () for c in con[1]
    ]
    noninstance_constraints = tuple(
        [
            hook
            for constraint in constraints
            for hook in constraint.hooks
            if hook[0] != ()
        ]
    )
    hook = conv.get_structure_hook(
        Annotated[(base, ConstraintAnnotated(noninstance_constraints))]
        if noninstance_constraints
        else base
    )

    @wraps(hook)
    def check_constraints(val: Any, type: Any) -> Any:
        res = hook(val, type)
        errors: list[Exception] = []
        for con in instance_constraint_hooks:
            try:
                if (error := con(res)) is not None:
                    errors.append(ConstraintError(error))
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise ConstraintGroupError("Constraint violations", errors, base)
        return res

    return check_constraints
