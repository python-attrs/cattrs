"""Class definitions using forward references."""

from __future__ import annotations

from typing import Generic, TypeVar

from attrs import define

T = TypeVar("T")


@define
class GenericClass(Generic[T]):
    t: T
