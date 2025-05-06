from typing import Protocol, TypeVar

__all__ = ["SimpleStructureHook"]
__all__ = [
    "Hook",
    "HookFactory",
    "SimpleStructureHook",
    "StructuredValue",
    "StructureHook",
    "TargetType",
    "UnstructuredValue",
    "UnstructureHook",
]

In = TypeVar("In")
T = TypeVar("T")

TargetType: TypeAlias = Any
UnstructuredValue: TypeAlias = Any
StructuredValue: TypeAlias = Any

StructureHook: TypeAlias = Callable[[UnstructuredValue, TargetType], StructuredValue]
UnstructureHook: TypeAlias = Callable[[StructuredValue], UnstructuredValue]

Hook = TypeVar("Hook", StructureHook, UnstructureHook)
HookFactory: TypeAlias = Callable[[TargetType], Hook]


class SimpleStructureHook(Protocol[In, T]):
    """A structure hook with an optional (ignored) second argument."""

    def __call__(self, _: In, /, cl=...) -> T: ...
