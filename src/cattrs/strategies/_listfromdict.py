"""The list-from-dict implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, get_args

from attrs import Attribute

from .. import BaseConverter, SimpleStructureHook
from ..dispatch import UnstructureHook
from ..fns import identity
from ..gen.typeddicts import is_typeddict

T = TypeVar("T")


def configure_list_from_dict(
    seq_type: list[T], field: str | Attribute, converter: BaseConverter
) -> tuple[SimpleStructureHook[Mapping, T], UnstructureHook]:
    """
    Configure a list subtype to be structured and unstructured into a dictionary,
    using a single field of the element as the dictionary key. This effectively
    ensures the resulting list is unique with regard to that field.

    List elements have to be able to be structured/unstructured using mappings.
    One field of the element is extracted into a dictionary key; the rest of the
    data is stored under that key.

    The types un/structuring into dictionaries by default are:
    * attrs classes and dataclasses
    * TypedDicts
    * named tuples when using the `namedtuple_dict_un/structure_factory`

    :param field: The name of the field to extract. When working with _attrs_ classes,
        consider passing in the attribute (as returned by `attrs.field(cls)`) for
        added safety.

    :return: A tuple of generated structure and unstructure hooks.

    .. versionadded:: 24.2.0

    """
    arg_type = get_args(seq_type)[0]

    arg_structure_hook = converter.get_structure_hook(arg_type, cache_result=False)

    if isinstance(field, Attribute):
        field = field.name

    def structure_hook(
        value: Mapping,
        _: Any = seq_type,
        _arg_type=arg_type,
        _arg_hook=arg_structure_hook,
        _field=field,
    ) -> list[T]:
        return [_arg_hook(v | {_field: k}, _arg_type) for k, v in value.items()]

    arg_unstructure_hook = converter.get_unstructure_hook(arg_type, cache_result=False)

    # TypedDicts can end up being unstructured via identity, in that case we make a copy
    # so we don't destroy the original.
    if is_typeddict(arg_type) and arg_unstructure_hook == identity:
        arg_unstructure_hook = dict

    def unstructure_hook(val: list[T], _arg_hook=arg_unstructure_hook) -> dict:
        return {(unstructured := _arg_hook(v)).pop(field): unstructured for v in val}

    return structure_hook, unstructure_hook
