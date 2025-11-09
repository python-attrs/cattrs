from typing import Protocol, TypeVar

__all__ = ["SimpleStructureHook"]

In_contra = TypeVar("In_contra", contravariant=True)
T_co = TypeVar("T_co", covariant=True)


class SimpleStructureHook(Protocol[In_contra, T_co]):
    """A structure hook with an optional (ignored) second argument."""

    def __call__(self, _: In_contra, /, cl=...) -> T_co: ...
