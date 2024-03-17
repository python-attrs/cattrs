from typing import Any, Callable, TypeAlias, TypeVar

#: Value validators take a single value and return a single value.
T = TypeVar("T")
Validator: TypeAlias = Callable[[T], Any]

ValidatorFactory: TypeAlias = Callable[[bool], Validator[T]]
