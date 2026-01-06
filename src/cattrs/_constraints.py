from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Annotated, Any

from attrs import frozen

from .annotated import split_from_annotated
from .constraints import ConstraintAnnotated, ConstraintPathSentinel
from .errors import ConstraintError, ConstraintGroupError

if TYPE_CHECKING:
    from .converters import BaseConverter
    from .dispatch import StructureHook


@frozen(slots=False, init=False)
class _ValDummy:
    """A validation dummy, used to gather the validation hooks."""

    def __init__(self, path: tuple[str, ...]) -> None:
        # We use a dotted name in `__dict__` to avoid clashes in `getattr`
        self.__dict__[".path"] = path

    def __getattr__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))

    def __getitem__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))

    def __iter__(self):
        yield _ValDummy(path=(*self.__dict__[".path"], ConstraintPathSentinel.EACH))


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
