"""Preconfigured converters for pyyaml."""
from datetime import datetime

from .._compat import FrozenSetSubscriptable
from ..converters import GenConverter
from . import validate_datetime


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the pyyaml library.

    * frozensets are serialized as lists
    * string enums are converted into strings explicitly
    """
    converter.register_unstructure_hook(
        str, lambda v: v if v.__class__ is str else v.value
    )
    converter.register_structure_hook(datetime, validate_datetime)


def make_converter(*args, **kwargs) -> GenConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        FrozenSetSubscriptable: list,
    }
    res = GenConverter(*args, **kwargs)
    configure_converter(res)

    return res
