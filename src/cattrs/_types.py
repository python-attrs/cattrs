"""Types for internal use."""

from __future__ import annotations

from dataclasses import Field
from types import FrameType, TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Tuple,
    Type,
    TypeVar,
    Union,
    final,
)

from typing_extensions import LiteralString, Protocol, TypeAlias

ExcInfo: TypeAlias = Tuple[Type[BaseException], BaseException, TracebackType]
OptExcInfo: TypeAlias = Union[ExcInfo, Tuple[None, None, None]]

# Superset of typing.AnyStr that also includes LiteralString
AnyOrLiteralStr = TypeVar("AnyOrLiteralStr", str, bytes, LiteralString)

# Represents when str or LiteralStr is acceptable. Useful for string processing
# APIs where literalness of return value depends on literalness of inputs
StrOrLiteralStr = TypeVar("StrOrLiteralStr", LiteralString, str)

# Objects suitable to be passed to sys.setprofile, threading.setprofile, and similar
ProfileFunction: TypeAlias = Callable[[FrameType, str, Any], object]

# Objects suitable to be passed to sys.settrace, threading.settrace, and similar
TraceFunction: TypeAlias = Callable[[FrameType, str, Any], Union["TraceFunction", None]]


# Copied over from https://github.com/hauntsaninja/useful_types/blob/main/useful_types/experimental.py
# Might not work as expected for pyright, see
#   https://github.com/python/typeshed/pull/9362
#   https://github.com/microsoft/pyright/issues/4339
@final
class DataclassLike(Protocol):
    """Abstract base class for all dataclass types.

    Mainly useful for type-checking.
    """

    __dataclass_fields__: ClassVar[dict[str, Field[Any]]] = {}

    # we don't want type checkers thinking this is a protocol member; it isn't
    if not TYPE_CHECKING:

        def __init_subclass__(cls):
            raise TypeError(
                "Use the @dataclass decorator to create dataclasses, "
                "rather than subclassing dataclasses.DataclassLike"
            )
