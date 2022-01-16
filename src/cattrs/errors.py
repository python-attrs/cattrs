from typing import Dict, Type

from attr import define


class StructureHandlerNotFoundError(Exception):
    """Error raised when structuring cannot find a handler for converting inputs into :attr:`type_`."""

    def __init__(self, message: str, type_: Type) -> None:
        super().__init__(message)
        self.type_ = type_


class ValidationError(Exception):
    pass


@define
class IterableValidationError(ValidationError):
    """Iterable validation errors.

    A dictionary of indices to errors for the element at that index.
    """

    errors_by_index: Dict[int, Exception]


@define
class ClassValidationError(ValidationError):
    """Raised when validating a class if any attributes are invalid."""

    errors_by_attribute: Dict[str, Exception]


@define
class MappingValidationError(ValidationError):
    """Mapping validation errors.

    A dictionary of element indices to key validation errors, and
    a dictionary of keys to value validation errors.
    """

    key_errors: Dict[int, Exception]
    value_errors: Dict[str, Exception]
