from __future__ import annotations

from typing import Dict, Type, TypeVar

from .._compat import get_args, get_origin


def generate_mapping(cl: Type, old_mapping: Dict[str, type]) -> Dict[str, type]:
    mapping = {}

    # To handle the cases where classes in the typing module are using
    # the GenericAlias structure but aren’t a Generic and hence
    # end up in this function but do not have an `__parameters__`
    # attribute. These classes are interface types, for example
    # `typing.Hashable`.
    parameters = getattr(get_origin(cl), "__parameters__", None)
    if parameters is None:
        return old_mapping

    for p, t in zip(parameters, get_args(cl)):
        if isinstance(t, TypeVar):
            continue
        mapping[p.__name__] = t

    if not mapping:
        return old_mapping

    return mapping
