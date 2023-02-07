from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from attr import Attribute

if TYPE_CHECKING:  # pragma: no cover
    from cattr.converters import BaseConverter


def find_structure_handler(
    a: Attribute, type: Any, c: BaseConverter, prefer_attrs_converters: bool = False
) -> Optional[Callable[[Any, Any], Any]]:
    """Find the appropriate structure handler to use.

    Return `None` if no handler should be used.
    """
    if a.converter is not None and prefer_attrs_converters:
        # If the user as requested to use attrib converters, use nothing
        # so it falls back to that.
        handler = None
    elif a.converter is not None and not prefer_attrs_converters and type is not None:
        handler = c._structure_func.dispatch(type)
        if handler == c._structure_error:
            handler = None
    elif type is not None:
        handler = c._structure_func.dispatch(type)
    else:
        handler = c.structure
    return handler
