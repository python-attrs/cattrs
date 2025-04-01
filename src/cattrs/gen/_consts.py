from __future__ import annotations

from threading import local
from typing import Any, Callable

from attrs import frozen


@frozen
class AttributeOverride:
    omit_if_default: bool | None = None
    rename: str | None = None
    location: str | tuple[str] | None = None,
    omit: bool | None = None  # Omit the field completely.
    omit_if: Callable[[Any, Any, Any], bool] | None = None # Omit if callable returns True.
    struct_hook: Callable[[Any, Any], Any] | None = None  # Structure hook to use.
    unstruct_hook: Callable[[Any], Any] | None = None  # Structure hook to use.


neutral = AttributeOverride()
already_generating = local()
