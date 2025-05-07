"""Useful internal functions."""

from functools import wraps
from typing import Any, Callable, NoReturn, TypeVar

from ._compat import TypeAlias
from .errors import StructureHandlerNotFoundError
from .types import StructuredValue, StructureHook, TargetType, UnstructuredValue

T = TypeVar("T")

Predicate: TypeAlias = Callable[[Any], bool]
"""A predicate function determines if a type can be handled."""


def identity(obj: T) -> T:
    """The identity function."""
    return obj


def bypass(target: type, structure_hook: StructureHook) -> StructureHook:
    """Bypass structure hook when given object of target type."""

    @wraps(structure_hook)
    def wrapper(obj: UnstructuredValue, cl: TargetType) -> StructuredValue:
        return obj if type(obj) is target else structure_hook(obj, cl)

    return wrapper


def raise_error(_, cl: Any) -> NoReturn:
    """At the bottom of the condition stack, we explode if we can't handle it."""
    msg = f"Unsupported type: {cl!r}. Register a structure hook for it."
    raise StructureHandlerNotFoundError(msg, type_=cl)
