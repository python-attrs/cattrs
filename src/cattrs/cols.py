"""Utility functions for collections."""

from __future__ import annotations

from sys import version_info
from typing import TYPE_CHECKING, Any, Iterable, NamedTuple, Tuple, TypeVar

from ._compat import ANIES, is_bare, is_sequence, is_subclass
from .dispatch import StructureHook, UnstructureHook
from .errors import IterableValidationError, IterableValidationNote
from .fns import identity
from .gen import make_hetero_tuple_unstructure_fn

if TYPE_CHECKING:
    from .converters import BaseConverter

__all__ = [
    "is_namedtuple",
    "is_sequence",
    "list_structure_factory",
    "namedtuple_structure_factory",
    "namedtuple_unstructure_factory",
]

if version_info[:2] >= (3, 9):

    def is_namedtuple(type: Any) -> bool:
        """A predicate function for named tuples."""

        if is_subclass(type, tuple):
            for cl in type.mro():
                orig_bases = cl.__dict__.get("__orig_bases__", ())
                if NamedTuple in orig_bases:
                    return True
        return False

else:

    def is_namedtuple(type: Any) -> bool:
        """A predicate function for named tuples."""
        # This is tricky. It may not be possible for this function to be 100%
        # accurate, since it doesn't seem like we can distinguish between tuple
        # subclasses and named tuples reliably.

        if is_subclass(type, tuple):
            for cl in type.mro():
                if cl is tuple:
                    # No point going further.
                    break
                if "_fields" in cl.__dict__:
                    return True
        return False


def _is_passthrough(type: type[tuple], converter: BaseConverter) -> bool:
    """If all fields would be passed through, this class should not be processed
    either.
    """
    return all(
        converter.get_unstructure_hook(t) == identity
        for t in type.__annotations__.values()
    )


T = TypeVar("T")


def list_structure_factory(type: type, converter: BaseConverter) -> StructureHook:
    """A hook factory for structuring lists.

    Converts any given iterable into a list.
    """

    if is_bare(type) or type.__args__[0] in ANIES:

        def structure_list(obj: Iterable[T], _: type = type) -> list[T]:
            return list(obj)

        return structure_list

    elem_type = type.__args__[0]

    try:
        handler = converter.get_structure_hook(elem_type)
    except RecursionError:
        # Break the cycle by using late binding.
        handler = converter.structure

    if converter.detailed_validation:

        def structure_list(
            obj: Iterable[T], _: type = type, _handler=handler, _elem_type=elem_type
        ) -> list[T]:
            errors = []
            res = []
            ix = 0  # Avoid `enumerate` for performance.
            for e in obj:
                try:
                    res.append(handler(e, _elem_type))
                except Exception as e:
                    msg = IterableValidationNote(
                        f"Structuring {type} @ index {ix}", ix, elem_type
                    )
                    e.__notes__ = [*getattr(e, "__notes__", []), msg]
                    errors.append(e)
                finally:
                    ix += 1
            if errors:
                raise IterableValidationError(
                    f"While structuring {type!r}", errors, type
                )

            return res

    else:

        def structure_list(
            obj: Iterable[T], _: type = type, _handler=handler, _elem_type=elem_type
        ) -> list[T]:
            return [_handler(e, _elem_type) for e in obj]

    return structure_list


def namedtuple_unstructure_factory(
    type: type[tuple], converter: BaseConverter, unstructure_to: Any = None
) -> UnstructureHook:
    """A hook factory for unstructuring namedtuples.

    :param unstructure_to: Force unstructuring to this type, if provided.
    """

    if unstructure_to is None and _is_passthrough(type, converter):
        return identity

    return make_hetero_tuple_unstructure_fn(
        type,
        converter,
        unstructure_to=tuple if unstructure_to is None else unstructure_to,
        type_args=tuple(type.__annotations__.values()),
    )


def namedtuple_structure_factory(
    type: type[tuple], converter: BaseConverter
) -> StructureHook:
    """A hook factory for structuring namedtuples."""
    # We delegate to the existing infrastructure for heterogenous tuples.
    hetero_tuple_type = Tuple[tuple(type.__annotations__.values())]
    base_hook = converter.get_structure_hook(hetero_tuple_type)
    return lambda v, _: type(*base_hook(v, hetero_tuple_type))
