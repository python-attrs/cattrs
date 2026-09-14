from collections.abc import Callable, Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any

from ._compat import has

if TYPE_CHECKING:
    from .converters import BaseConverter


def _needs_recursive_unstructure(value: Any) -> bool:
    if isinstance(value, Enum) or has(value.__class__):
        return True
    if isinstance(value, tuple | list | set | frozenset):
        return any(_needs_recursive_unstructure(v) for v in value)
    if isinstance(value, Mapping):
        return any(
            _needs_recursive_unstructure(k) or _needs_recursive_unstructure(v)
            for k, v in value.items()
        )
    return False


def enum_unstructure_factory(
    type: type[Enum], converter: "BaseConverter"
) -> Callable[[Enum], Any]:
    """A factory for generating enum unstructure hooks.

    If the enum is a typed enum (has `_value_`), we use the underlying value's hook.
    Otherwise, we only use the converter when the values are known to need it.
    """
    if "_value_" in type.__annotations__ or any(
        _needs_recursive_unstructure(member.value) for member in type
    ):
        return lambda e: converter.unstructure(e.value)

    return lambda e: e.value


def enum_structure_factory(
    type: type[Enum], converter: "BaseConverter"
) -> Callable[[Any, type[Enum]], Enum]:
    """A factory for generating enum structure hooks.

    If the enum is a typed enum (has `_value_`), we structure the value first.
    Otherwise, we use the value directly.
    """
    if "_value_" in type.__annotations__:
        val_type = type.__annotations__["_value_"]
        val_hook = converter.get_structure_hook(val_type)
        return lambda v, _: type(val_hook(v, val_type))

    return lambda v, _: type(v)
