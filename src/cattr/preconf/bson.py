"""Preconfigured converters for bson."""
from datetime import datetime

from .._compat import Set
from ..converters import GenConverter
from . import validate_datetime


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the bson library.

    * sets are serialized as lists
    """
    converter.register_structure_hook(datetime, validate_datetime)


def make_converter(*args, **kwargs) -> GenConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
    }
    res = GenConverter(*args, **kwargs)
    configure_converter(res)

    return res
