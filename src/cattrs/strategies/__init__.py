"""High level strategies for converters."""

from ._class_methods import use_class_methods
from ._subclasses import include_subclasses
from ._unions import configure_tagged_union, configure_union_passthrough, configure_union_single_collection_dispatch

__all__ = [
    "configure_tagged_union",
    "configure_union_passthrough",
    "configure_union_single_collection_dispatch",
    "include_subclasses",
    "use_class_methods",
]
