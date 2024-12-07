"""High level strategies for converters."""

from ._class_methods import use_class_methods
from ._listfromdict import configure_list_from_dict
from ._subclasses import include_subclasses
from ._unions import configure_tagged_union, configure_union_passthrough

__all__ = [
    "configure_list_from_dict",
    "configure_tagged_union",
    "configure_union_passthrough",
    "include_subclasses",
    "use_class_methods",
]
