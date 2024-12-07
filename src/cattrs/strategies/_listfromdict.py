"""The list-from-dict implementation."""

from collections.abc import Mapping
from typing import Any, TypeVar, get_args

from .. import BaseConverter, SimpleStructureHook
from ..dispatch import UnstructureHook

T = TypeVar("T")


def configure_list_from_dict(
    seq_type: list[T], field: str, converter: BaseConverter
) -> tuple[SimpleStructureHook[Mapping, T], UnstructureHook]:
    """
    Configure a list subtype to be structured and unstructured using a dictionary.

    List elements have to be an attrs class or a dataclass. One field of the element
    type is extracted into a dictionary key; the rest of the data is stored under that
    key.

    """
    arg_type = get_args(seq_type)[0]

    arg_structure_hook = converter.get_structure_hook(arg_type, cache_result=False)

    def structure_hook(
        value: Mapping, type: Any = seq_type, _arg_type=arg_type
    ) -> list[T]:
        return [arg_structure_hook(v | {field: k}, _arg_type) for k, v in value.items()]

    arg_unstructure_hook = converter.get_unstructure_hook(arg_type, cache_result=False)

    def unstructure_hook(val: list[T]) -> dict:
        return {
            (unstructured := arg_unstructure_hook(v)).pop(field): unstructured
            for v in val
        }

    return structure_hook, unstructure_hook
