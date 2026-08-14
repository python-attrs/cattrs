from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any
from typing import Type as _Type

if TYPE_CHECKING:
    from .converters import BaseConverter


def _enum_misuse_message(expected: type[Enum], got: Any) -> str:
    return (
        f"Expected an instance of {expected!r} to unstructure, got "
        f"{got!r} of type {got.__class__!r} instead. This usually means a "
        f"raw value (e.g. {expected.__name__}.MEMBER.value) or some other "
        f"non-enum value was assigned to an attribute or variable that is "
        f"typed as this enum, instead of an actual {expected.__name__} "
        f"member."
    )


def enum_unstructure_factory(
    type: type[Enum], converter: "BaseConverter"
) -> Callable[[Enum], Any]:
    """A factory for generating enum unstructure hooks.

    If the enum is a typed enum (has `_value_`), we use the underlying value's hook.
    Otherwise, we use the value directly.
    """
    if "_value_" in type.__annotations__:

        def unstructure_typed_enum(
            e: Enum, _cl: _Type[Enum] = type, _converter: "BaseConverter" = converter
        ) -> Any:
            if not isinstance(e, _cl):
                raise TypeError(_enum_misuse_message(_cl, e))
            return _converter.unstructure(e.value)

        return unstructure_typed_enum

    def unstructure_enum(e: Enum, _cl: _Type[Enum] = type) -> Any:
        if not isinstance(e, _cl):
            raise TypeError(_enum_misuse_message(_cl, e))
        return e.value

    return unstructure_enum


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
