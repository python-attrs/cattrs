from functools import cache
from importlib import import_module
from types import ModuleType
from typing import NoReturn

from ...converters import Converter
from ...fns import bypass


def register_extra_types(converter: Converter, *classes: type) -> None:
    """
    TODO: Add docs
    """
    for cl in classes:
        if not isinstance(cl, type):
            raise TypeError("Type required instead of object")

        struct_hook = get_module(cl).gen_structure_hook(cl, converter)
        if struct_hook is None:
            raise_unsupported(cl)
        converter.register_structure_hook(cl, bypass(cl, struct_hook))

        unstruct_hook = get_module(cl).gen_unstructure_hook(cl, converter)
        if unstruct_hook is None:
            raise_unsupported(cl)
        converter.register_unstructure_hook(cl, unstruct_hook)


@cache
def get_module(cl: type) -> ModuleType:
    modname = getattr(cl, "__module__", "builtins")
    try:
        return import_module(f"cattrs.strategies._extra_types._{modname}")
    except ModuleNotFoundError:
        raise_unsupported(cl)


def raise_unexpected_structure(target: type, cl: type) -> NoReturn:
    raise TypeError(f"Unable to structure registered extra type {target} from {cl}")


def raise_unsupported(cl: type) -> NoReturn:
    raise ValueError(f"Type {cl} is not supported by register_extra_types strategy")
