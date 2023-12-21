"""Utilities for union (sum type) disambiguation."""
from __future__ import annotations

from collections import defaultdict
from functools import reduce
from operator import or_
from typing import TYPE_CHECKING, Any, Callable, Mapping, Union

from attrs import NOTHING, Attribute, AttrsInstance, fields, fields_dict

from ._compat import NoneType, get_args, get_origin, has, is_literal, is_union_type
from .gen import AttributeOverride

if TYPE_CHECKING:
    from .converters import BaseConverter

__all__ = ["is_supported_union", "create_default_dis_func"]


def is_supported_union(typ: Any) -> bool:
    """Whether the type is a union of attrs classes."""
    return is_union_type(typ) and all(
        e is NoneType or has(get_origin(e) or e) for e in typ.__args__
    )


def create_default_dis_func(
    converter: BaseConverter, *classes: type[AttrsInstance], use_literals: bool = True
) -> Callable[[Mapping[Any, Any]], type[Any] | None]:
    """Given attrs classes, generate a disambiguation function.

    The function is based on unique fields without defaults or unique values.

    :param use_literals: Whether to try using fields annotated as literals for
        disambiguation.
    """
    if len(classes) < 2:
        raise ValueError("At least two classes required.")

    overrides = [
        getattr(converter.get_structure_hook(c), "overrides", {}) for c in classes
    ]

    # first, attempt for unique values
    if use_literals:
        # requirements for a discriminator field:
        # (... TODO: a single fallback is OK)
        #  - it must always be enumerated
        cls_candidates = [
            {at.name for at in fields(get_origin(cl) or cl) if is_literal(at.type)}
            for cl in classes
        ]

        # literal field names common to all members
        discriminators: set[str] = cls_candidates[0]
        for possible_discriminators in cls_candidates:
            discriminators &= possible_discriminators

        best_result = None
        best_discriminator = None
        for discriminator in discriminators:
            # maps Literal values (strings, ints...) to classes
            mapping = defaultdict(list)

            for cl in classes:
                for key in get_args(
                    fields_dict(get_origin(cl) or cl)[discriminator].type
                ):
                    mapping[key].append(cl)

            if best_result is None or max(len(v) for v in mapping.values()) <= max(
                len(v) for v in best_result.values()
            ):
                best_result = mapping
                best_discriminator = discriminator

        if (
            best_result
            and best_discriminator
            and max(len(v) for v in best_result.values()) != len(classes)
        ):
            final_mapping = {
                k: v[0] if len(v) == 1 else Union[tuple(v)]
                for k, v in best_result.items()
            }

            def dis_func(data: Mapping[Any, Any]) -> type | None:
                if not isinstance(data, Mapping):
                    raise ValueError("Only input mappings are supported.")
                return final_mapping[data[best_discriminator]]

            return dis_func

    # next, attempt for unique keys

    # NOTE: This could just as well work with just field availability and not
    #  uniqueness, returning Unions ... it doesn't do that right now.
    cls_and_attrs = [
        (cl, _usable_attribute_names(cl, override))
        for cl, override in zip(classes, overrides)
    ]
    # For each class, attempt to generate a single unique required field.
    uniq_attrs_dict: dict[str, type] = {}

    # We start from classes with fewest unique fields.
    cls_and_attrs.sort(key=lambda c_a: len(c_a[1]))

    fallback = None  # If none match, try this.

    for cl, (cl_reqs, back_map) in cls_and_attrs:
        other_classes = [c_and_a for c_and_a in cls_and_attrs if c_and_a[0] is not cl]
        other_reqs = reduce(or_, (c_a[1][0] for c_a in other_classes))
        uniq = cl_reqs - other_reqs

        # We want a unique attribute with no default.
        cl_fields = fields(get_origin(cl) or cl)
        for maybe_renamed_attr_name in uniq:
            orig_name = back_map[maybe_renamed_attr_name]
            if getattr(cl_fields, orig_name).default is NOTHING:
                break
        else:
            if fallback is None:
                fallback = cl
                continue
            raise TypeError(f"{cl} has no usable non-default attributes")
        uniq_attrs_dict[maybe_renamed_attr_name] = cl

    def dis_func(data: Mapping[Any, Any]) -> type[AttrsInstance] | None:
        if not isinstance(data, Mapping):
            raise ValueError("Only input mappings are supported")
        for k, v in uniq_attrs_dict.items():
            if k in data:
                return v
        return fallback

    return dis_func


create_uniq_field_dis_func = create_default_dis_func


def _overriden_name(at: Attribute, override: AttributeOverride | None) -> str:
    if override is None or override.rename is None:
        return at.name
    return override.rename


def _usable_attribute_names(
    cl: type[AttrsInstance], overrides: dict[str, AttributeOverride]
) -> tuple[set[str], dict[str, str]]:
    """Return renamed fields and a mapping to original field names."""
    res = set()
    mapping = {}

    for at in fields(get_origin(cl) or cl):
        res.add(n := _overriden_name(at, overrides.get(at.name)))
        mapping[n] = at.name

    return res, mapping
