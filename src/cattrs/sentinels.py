"""Support for Python 3.15 sentinel values.

.. versionadded:: NEXT
"""

from typing import TYPE_CHECKING, Any, Union

from ._compat import NoneType, is_union_type, sentinel
from .errors import CattrsError

if TYPE_CHECKING:
    from .converters import BaseConverter
    from .dispatch import StructureHook, UnstructureHook


def is_sentinel(typ: Any) -> bool:
    """Is this a Python 3.15+ sentinel instance?

    .. versionadded:: NEXT
    """
    return sentinel is not None and isinstance(typ, sentinel)


def sentinel_unstructure(value: Any) -> str:
    """Serialize a sentinel by name.

    .. versionadded:: NEXT
    """
    return value.__name__


def sentinel_class_unstructure_factory(
    _: Any, converter: "BaseConverter"
) -> "UnstructureHook":
    """Dispatch sentinel values by instance only after matching their runtime class.

    .. versionadded:: NEXT
    """
    dispatch = converter._unstructure_func.dispatch

    def unstructure_sentinel(value: Any) -> Any:
        return dispatch(value)(value)

    return unstructure_sentinel


def sentinel_structure(value: Any, target: Any) -> Any:
    """Restore a sentinel from its name.

    .. versionadded:: NEXT
    """
    if isinstance(value, str) and value == target.__name__:
        return target
    raise CattrsError(f"{value!r} is not the name of sentinel {target!r}")


def is_sentinel_union(typ: Any) -> bool:
    """Is this a union containing a Python 3.15+ sentinel instance?

    .. versionadded:: NEXT
    """
    return is_union_type(typ) and any(is_sentinel(t) for t in typ.__args__)


def sentinel_union_structure_factory(
    union: Any, converter: "BaseConverter"
) -> "StructureHook":
    """Match sentinel names before structuring the remaining union members.

    .. versionadded:: NEXT
    """
    sentinels = [t for t in union.__args__ if is_sentinel(t)]
    by_name = {t.__name__: t for t in sentinels}
    if len(by_name) != len(sentinels):
        raise ValueError(f"Sentinels in {union!r} must have distinct names")
    hooks = {name: converter.get_structure_hook(t) for name, t in by_name.items()}
    has_none = NoneType in union.__args__
    rest = tuple(t for t in union.__args__ if not is_sentinel(t) and t is not NoneType)
    if rest:
        target = rest[0] if len(rest) == 1 else Union[rest]
        hook = converter.get_structure_hook(target)

    def structure_sentinel_union(value: Any, _: Any) -> Any:
        if value is None and has_none:
            return None
        if isinstance(value, str) and value in by_name:
            return hooks[value](value, by_name[value])
        if rest:
            return hook(value, target)
        raise CattrsError(f"{value!r} is not a sentinel name in {union!r}")

    return structure_sentinel_union
