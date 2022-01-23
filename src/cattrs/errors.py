from typing import Type

from cattr._compat import ExceptionGroup


class StructureHandlerNotFoundError(Exception):
    """Error raised when structuring cannot find a handler for converting inputs into :attr:`type_`."""

    def __init__(self, message: str, type_: Type) -> None:
        super().__init__(message)
        self.type_ = type_


class BaseValidationError(ExceptionGroup):
    cl: Type

    def __new__(cls, message, excs, cl: Type):
        obj = super().__new__(cls, message, excs)
        obj.cl = cl
        return obj

    def derive(self, excs):
        return ClassValidationError(self.message, excs, self.cl)


class IterableValidationError(BaseValidationError):
    """Raised when structuring an iterable."""
    pass


class ClassValidationError(BaseValidationError):
    """Raised when validating a class if any attributes are invalid."""
    pass
