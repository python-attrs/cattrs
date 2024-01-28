from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, Tuple

from ._compat import is_subclass
from .dispatch import StructureHook, UnstructureHook
from .fns import identity
from .gen import make_hetero_tuple_unstructure_fn

if TYPE_CHECKING:
    from .converters import BaseConverter


def is_namedtuple(type: Any) -> bool:
    """A predicate function for named tuples."""
    # This is tricky. It may not be possible for this function to be 100%
    # accurate, since it doesn't seem like we can distinguish between tuple
    # subclasses and named tuples reliably.

    if is_subclass(type, tuple):
        for cl in type.mro():
            orig_bases = cl.__dict__.get("__orig_bases__", ())
            if NamedTuple in orig_bases:
                return True
    return False


def is_passthrough(type: type[tuple], converter: BaseConverter) -> bool:
    """If all fields would be passed through, this class should not be processed
    either.
    """
    return all(
        converter.get_unstructure_hook(t) == identity
        for t in type.__annotations__.values()
    )


def namedtuple_unstructure_factory(
    type: type[tuple], converter: BaseConverter, unstructure_to: Any = None
) -> UnstructureHook:
    """A hook factory for unstructuring namedtuples.

    :param unstructure_to: Force unstructuring to this type, if provided.
    """

    if unstructure_to is None and is_passthrough(type, converter):
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
    hetero_tuple_type = Tuple[*type.__annotations__.values()]
    base_hook = converter.get_structure_hook(hetero_tuple_type)
    return lambda v, _: type(*base_hook(v, hetero_tuple_type))
