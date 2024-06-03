"""Cattrs validation."""

from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar, Union, overload

from attrs import NOTHING, frozen

from .._compat import Annotated, ExceptionGroup
from ..errors import (
    ClassValidationError,
    ForbiddenExtraKeysError,
    IterableValidationError,
    ValueValidationError,
)
from ._fluent import V, customize
from ._validators import (
    between,
    for_all,
    greater_than,
    ignoring_none,
    is_unique,
    len_between,
)

__all__ = [
    "between",
    "customize",
    "for_all",
    "format_exception",
    "greater_than",
    "ignoring_none",
    "is_unique",
    "len_between",
    "transform_error",
    "V",
    "ValidatorFactory",
]


@frozen
class VAnnotation:
    """Use this with Annotated to get validation."""

    validators: Tuple[Callable[[Any], Any]]

    def __init__(self, *validators: Callable[[Any], Any]):
        self.__attrs_init__(validators)


def format_exception(exc: BaseException, type: Union[type, None]) -> str:
    """The default exception formatter, handling the most common exceptions.

    The following exceptions are handled specially:

    * `KeyErrors` (`required field missing`)
    * `ValueErrors` (`invalid value for type, expected <type>` or just `invalid value`)
    * `TypeErrors` (`invalid value for type, expected <type>` and a couple special
      cases for iterables)
    * `cattrs.ForbiddenExtraKeysError`
    * some `AttributeErrors` (special cased for structing mappings)
    """
    if isinstance(exc, KeyError):
        res = "required field missing"
    elif isinstance(exc, ValueError):
        if type is not None:
            tn = type.__name__ if hasattr(type, "__name__") else repr(type)
            res = f"invalid value for type, expected {tn} ({exc.args[0]})"
        elif exc.args:
            res = f"invalid value ({exc.args[0]})"
        else:
            res = "invalid value"
    elif isinstance(exc, TypeError):
        if type is None:
            if exc.args[0].endswith("object is not iterable"):
                res = "invalid value for type, expected an iterable"
            else:
                res = f"invalid type ({exc})"
        else:
            tn = type.__name__ if hasattr(type, "__name__") else repr(type)
            res = f"invalid value for type, expected {tn}"
    elif isinstance(exc, ForbiddenExtraKeysError):
        res = f"extra fields found ({', '.join(exc.extra_fields)})"
    elif isinstance(exc, AttributeError) and exc.args[0].endswith(
        "object has no attribute 'items'"
    ):
        # This was supposed to be a mapping (and have .items()) but it something else.
        res = "expected a mapping"
    elif isinstance(exc, AttributeError) and exc.args[0].endswith(
        "object has no attribute 'copy'"
    ):
        # This was supposed to be a mapping (and have .copy()) but it something else.
        # Used for TypedDicts.
        res = "expected a mapping"
    else:
        res = f"unknown error ({exc})"

    return res


def transform_error(
    exc: Union[
        ClassValidationError,
        IterableValidationError,
        ValueValidationError,
        BaseException,
    ],
    path: str = "$",
    format_exception: Callable[
        [BaseException, Union[type, None]], str
    ] = format_exception,
) -> List[str]:
    """Transform an exception into a list of error messages.

    To get detailed error messages, the exception should be produced by a converter
    with `detailed_validation` set.

    By default, the error messages are in the form of `{description} @ {path}`.

    While traversing the exception and subexceptions, the path is formed:

    * by appending `.{field_name}` for fields in classes
    * by appending `[{int}]` for indices in iterables, like lists
    * by appending `[{str}]` for keys in mappings, like dictionaries

    :param exc: The exception to transform into error messages.
    :param path: The root path to use.
    :param format_exception: A callable to use to transform `Exceptions` into
        string descriptions of errors.

    .. versionadded:: 23.1.0
    """
    errors: List[str] = []
    if isinstance(exc, IterableValidationError):
        for e, note in exc.group_exceptions():
            p = f"{path}[{note.index!r}]"
            if isinstance(e, (ClassValidationError, IterableValidationError)):
                errors.extend(transform_error(e, p, format_exception))
            else:
                errors.append(f"{format_exception(e, note.type)} @ {p}")
    elif isinstance(exc, ClassValidationError):
        with_notes, without = exc.group_exceptions()
        for exc, note in with_notes:
            p = f"{path}.{note.name}"
            if isinstance(exc, ExceptionGroup):
                errors.extend(transform_error(exc, p, format_exception))
            else:
                errors.append(f"{format_exception(exc, note.type)} @ {p}")
        for exc in without:
            errors.append(f"{format_exception(exc, None)} @ {path}")
    elif isinstance(exc, ValueValidationError):
        # This is a value validation error, which we should just flatten.
        for inner in exc.exceptions:
            errors.append(f"{format_exception(inner, None)} @ {path}")
    elif isinstance(exc, ExceptionGroup):
        # Likely from a nested validator, needs flattening.
        errors.extend(
            [
                line
                for inner in exc.exceptions
                for line in transform_error(inner, path, format_exception)
            ]
        )
    else:
        errors.append(f"{format_exception(exc, None)} @ {path}")
    return errors


T = TypeVar("T")
E = TypeVar("E")
TV = TypeVar("TV")


@overload
def ensure(
    type: Type[List[T]], *validators: Callable[[List[T]], Any], elems: Type[E]
) -> Type[List[E]]: ...


@overload
def ensure(
    type: Type[Dict],
    *validators: Callable[[Dict], Any],
    keys: Type[E],
    values: Type[TV],
) -> Type[Dict[E, TV]]: ...


@overload
def ensure(type: Type[T], *validators: Callable[[T], Any]) -> Type[T]: ...


def ensure(type, *validators, elems=NOTHING, keys=NOTHING, values=NOTHING):
    """Ensure validators run when structuring the given type."""
    if elems is not NOTHING:
        # These are lists.
        if not validators:
            return type[elems]
        return Annotated[type[elems], VAnnotation(*validators)]
    if keys is not NOTHING or values is not NOTHING:
        if not validators:
            return type[keys, values]
        return Annotated[type[keys, values], VAnnotation(*validators)]
    return Annotated[type, VAnnotation(*validators)]
