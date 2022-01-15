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
    errors_by_index: Dict[int, Exception]


@define
class ClassValidationError(ValidationError):
    """Raised when validating a class if any attributes are invalid."""

    errors_by_attribute: Dict[str, Exception]
