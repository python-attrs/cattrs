"""Hooks and hook factories for validation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._compat import Annotated, ExceptionGroup, is_annotated
from ..dispatch import StructureHook
from . import VAnnotation

if TYPE_CHECKING:
    from ..converters import BaseConverter


def get_validator_annotation(type: Any) -> tuple[VAnnotation, Any] | None:
    if is_annotated(type):
        args = type.__metadata__
        for arg in args:
            if isinstance(arg, VAnnotation):
                new_args = tuple(a for a in args[1:] if a is not arg)
                if new_args:
                    return Annotated(type.__origin__, *new_args)  # type: ignore
                return arg, type.__origin__
    return None


def is_validated(type: Any) -> bool:
    """The predicate for validated annotations."""
    return get_validator_annotation(type) is not None


def validator_factory(type: Any, converter: BaseConverter) -> StructureHook:
    res = get_validator_annotation(type)
    assert res is not None
    val_annotation, type = res

    base_hook = converter.get_structure_hook(type)

    if converter.detailed_validation:

        def validating_hook(val: Any, _: Any) -> Any:
            res = base_hook(val, type)
            errors = []
            for validator in val_annotation.validators:
                try:
                    if validator(res) is False:
                        raise ValueError(f"Validation failed for {res}")
                except Exception as exc:
                    errors.append(exc)
            if errors:
                raise ExceptionGroup("Value validation failed", errors)
            return res

    else:

        def validating_hook(val: Any, _: Any) -> Any:
            res = base_hook(val, type)
            for validator in val_annotation.validators:
                if validator(res) is False:
                    raise ValueError(f"Validation failed for {res}")
            return res

    return validating_hook
