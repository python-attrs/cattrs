from .converters import BaseConverter, Converter, GenConverter, UnstructureStrategy
from .gen import override

__all__ = (
    "BaseConverter",
    "Converter",
    "GenConverter",
    "UnstructureStrategy",
    "global_converter",
    "override",
    "structure",
    "structure_attrs_fromdict",
    "structure_attrs_fromtuple",
    "unstructure",
)
from cattrs import global_converter

unstructure = global_converter.unstructure
structure = global_converter.structure
structure_attrs_fromtuple = global_converter.structure_attrs_fromtuple
structure_attrs_fromdict = global_converter.structure_attrs_fromdict
register_structure_hook = global_converter.register_structure_hook
register_structure_hook_func = global_converter.register_structure_hook_func
register_unstructure_hook = global_converter.register_unstructure_hook
register_unstructure_hook_func = global_converter.register_unstructure_hook_func
