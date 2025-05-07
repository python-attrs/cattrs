"""High level strategies for converters."""

from ._class_methods import use_class_methods
from ._extra_types import register_extra_types
from ._subclasses import include_subclasses
from ._unions import configure_tagged_union, configure_union_passthrough

__all__ = [
    "configure_tagged_union",
    "configure_union_passthrough",
    "include_subclasses",
    "register_extra_types",
    "use_class_methods",
]
