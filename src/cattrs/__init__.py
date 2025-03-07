from typing import Final

from .converters import BaseConverter, Converter, GenConverter, UnstructureStrategy
from .errors import (
    AttributeValidationNote,
    BaseValidationError,
    ClassValidationError,
    ForbiddenExtraKeysError,
    IterableValidationError,
    IterableValidationNote,
    StructureHandlerNotFoundError,
)
from .gen import override
from .types import SimpleStructureHook
from .v import transform_error

__all__ = [
    "AttributeValidationNote",
    "BaseConverter",
    "BaseValidationError",
    "ClassValidationError",
    "Converter",
    "ForbiddenExtraKeysError",
    "GenConverter",
    "IterableValidationError",
    "IterableValidationNote",
    "SimpleStructureHook",
    "StructureHandlerNotFoundError",
    "UnstructureStrategy",
    "get_structure_hook",
    "get_unstructure_hook",
    "global_converter",
    "override",
    "register_structure_hook",
    "register_structure_hook_func",
    "register_unstructure_hook",
    "register_unstructure_hook_func",
    "structure",
    "structure_attrs_fromdict",
    "structure_attrs_fromtuple",
    "transform_error",
    "unstructure",
]

#: The global converter. Prefer creating your own if customizations are required.
global_converter: Final = Converter()

unstructure = global_converter.unstructure
structure = global_converter.structure
structure_attrs_fromtuple = global_converter.structure_attrs_fromtuple
structure_attrs_fromdict = global_converter.structure_attrs_fromdict
register_structure_hook = global_converter.register_structure_hook
register_structure_hook_func = global_converter.register_structure_hook_func
register_unstructure_hook = global_converter.register_unstructure_hook
register_unstructure_hook_func = global_converter.register_unstructure_hook_func
get_structure_hook: Final = global_converter.get_structure_hook
get_unstructure_hook: Final = global_converter.get_unstructure_hook
