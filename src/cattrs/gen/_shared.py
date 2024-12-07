from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, get_type_hints

from attrs import NOTHING, Attribute, Factory

from .._compat import is_bare_final
from ..dispatch import StructureHook
from ..errors import StructureHandlerNotFoundError
from ..fns import raise_error

if TYPE_CHECKING:
    from collections.abc import Mapping
    from ..converters import BaseConverter

T = TypeVar("T")

def find_structure_handler(
    a: Attribute, type: Any, c: BaseConverter, prefer_attrs_converters: bool = False
) -> StructureHook | None:
    """Find the appropriate structure handler to use.

    Return `None` if no handler should be used.
    """
    try:
        if a.converter is not None and prefer_attrs_converters:
            # If the user as requested to use attrib converters, use nothing
            # so it falls back to that.
            handler = None
        elif (
            a.converter is not None and not prefer_attrs_converters and type is not None
        ):
            try:
                handler = c.get_structure_hook(type, cache_result=False)
            except StructureHandlerNotFoundError:
                handler = None
            else:
                # The legacy way, should still work.
                if handler == raise_error:
                    handler = None
        elif type is not None:
            if (
                is_bare_final(type)
                and a.default is not NOTHING
                and not isinstance(a.default, Factory)
            ):
                # This is a special case where we can use the
                # type of the default to dispatch on.
                type = a.default.__class__
                handler = c.get_structure_hook(type, cache_result=False)
                if handler == c._structure_call:
                    # Finals can't really be used with _structure_call, so
                    # we wrap it so the rest of the toolchain doesn't get
                    # confused.

                    def handler(v, _, _h=handler):
                        return _h(v, type)

            else:
                handler = c.get_structure_hook(type, cache_result=False)
        else:
            handler = c.structure
        return handler
    except RecursionError:
        # This means we're dealing with a reference cycle, so use late binding.
        return c.structure


def get_fields_annotated_by(cls: type, annotation_type: type[T] | T) -> dict[str, T]:
    type_hints = get_type_hints(cls, include_extras=True)
    # Support for both AttributeOverride and AttributeOverride()
    annotation_type_ = annotation_type if isinstance(annotation_type, type) else type(annotation_type)

    # First pass of filtering to get only fields with annotations
    fields_with_annotations = (
        (field_name, param_spec.__metadata__)
        for field_name, param_spec in type_hints.items()
        if hasattr(param_spec, "__metadata__")
    )

    # Now that we have fields with ANY annotations, we need to remove unwanted annotations.
    fields_with_specific_annotation = (
        (
            field_name,
            next((a for a in annotations if isinstance(a, annotation_type_)), None),
        )
        for field_name, annotations in fields_with_annotations
    )

    # We still might have some `None` values from previous filtering.
    return {field_name: annotation for field_name, annotation in fields_with_specific_annotation if annotation}
