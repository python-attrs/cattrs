from typing import Type


class StructureHandlerNotFoundError(Exception):
    """Error raised when structuring cannot find a handler for converting inputs into :attr:`type_`."""

    def __init__(self, message: str, type_: Type) -> None:
        super().__init__(message)
        self.type_ = type_
