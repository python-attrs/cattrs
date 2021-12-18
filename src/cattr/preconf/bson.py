"""Preconfigured converters for bson."""
from datetime import datetime
from typing import Any

from .._compat import Set, is_mapping
from ..converters import GenConverter
from . import validate_datetime


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the bson library.

    * sets are serialized as lists
    * non-string mapping keys are coerced into strings when unstructuring
    """

    def gen_unstructure_mapping(cl: Any, unstructure_to=None):
        key_handler = str
        args = getattr(cl, "__args__", None)
        if args and issubclass(args[0], str):
            key_handler = None
        return converter.gen_unstructure_mapping(
            cl, unstructure_to=unstructure_to, key_handler=key_handler
        )

    converter._unstructure_func.register_func_list(
        [(is_mapping, gen_unstructure_mapping, True)]
    )

    converter.register_structure_hook(datetime, validate_datetime)


def make_converter(*args, **kwargs) -> GenConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
    }
    res = GenConverter(*args, **kwargs)
    configure_converter(res)

    return res
