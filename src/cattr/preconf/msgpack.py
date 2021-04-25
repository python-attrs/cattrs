"""Preconfigured converters for msgpack."""
from datetime import datetime, timezone

from .._compat import Set
from ..converters import GenConverter


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the msgpack library.

    * datetimes are serialized as timestamp floats
    * sets are serialized as lists
    """
    converter.register_unstructure_hook(datetime, lambda v: v.timestamp())
    converter.register_structure_hook(
        datetime, lambda v, _: datetime.fromtimestamp(v, timezone.utc)
    )


def make_converter(*args, **kwargs) -> GenConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
    }
    res = GenConverter(*args, **kwargs)
    configure_converter(res)

    return res
