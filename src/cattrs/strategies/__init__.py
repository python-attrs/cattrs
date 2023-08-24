"""High level strategies for converters."""
from ._class_methods import use_class_methods
from ._subclasses import include_subclasses
from ._unions import configure_tagged_union

__all__ = ["configure_tagged_union", "include_subclasses", "use_class_methods"]
