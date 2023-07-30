"""Utilities for union (sum type) disambiguation."""
from collections import OrderedDict, defaultdict
from functools import reduce
from operator import or_
from typing import Any, Callable, Dict, Mapping, Optional, Type, Union

from attr import NOTHING, fields, fields_dict

from cattrs._compat import get_args, get_origin, is_literal


def create_default_dis_func(
    *classes: Type[Any],
) -> Callable[[Mapping[Any, Any]], Optional[Type[Any]]]:
    """Given attr classes, generate a disambiguation function.

    The function is based on unique fields or unique values."""
    if len(classes) < 2:
        raise ValueError("At least two classes required.")

    # first, attempt for unique values

    # requirements for a discriminator field:
    # (... TODO: a single fallback is OK)
    #  - it must be *required*
    #  - it must always be enumerated
    cls_candidates = [
        {
            at.name
            for at in fields(get_origin(cl) or cl)
            if at.default is NOTHING and is_literal(at.type)
        }
        for cl in classes
    ]

    discriminators = cls_candidates[0]
    for possible_discriminators in cls_candidates:
        discriminators &= possible_discriminators

    best_result = None
    best_discriminator = None
    for discriminator in discriminators:
        mapping = defaultdict(list)

        for cl in classes:
            for key in get_args(fields_dict(get_origin(cl) or cl)[discriminator].type):
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
            k: v[0] if len(v) == 1 else Union[tuple(v)] for k, v in best_result.items()
        }

        def dis_func(data: Mapping[Any, Any]) -> Optional[Type]:
            if not isinstance(data, Mapping):
                raise ValueError("Only input mappings are supported.")
            return final_mapping[data[best_discriminator]]

        return dis_func

    # next, attempt for unique keys

    # NOTE: This could just as well work with just field availability and not
    #  uniqueness, returning Unions ... it doesn't do that right now.
    cls_and_attrs = [
        (cl, {at.name for at in fields(get_origin(cl) or cl)}) for cl in classes
    ]
    if len([attrs for _, attrs in cls_and_attrs if len(attrs) == 0]) > 1:
        raise ValueError("At least two classes have no attributes.")
    # TODO: Deal with a single class having no required attrs.
    # For each class, attempt to generate a single unique required field.
    uniq_attrs_dict: Dict[str, Type] = OrderedDict()
    cls_and_attrs.sort(key=lambda c_a: -len(c_a[1]))

    fallback = None  # If none match, try this.

    for i, (cl, cl_reqs) in enumerate(cls_and_attrs):
        other_classes = cls_and_attrs[i + 1 :]
        if other_classes:
            other_reqs = reduce(or_, (c_a[1] for c_a in other_classes))
            uniq = cl_reqs - other_reqs
            if not uniq:
                m = f"{cl} has no usable unique attributes."
                raise ValueError(m)
            # We need a unique attribute with no default.
            cl_fields = fields(get_origin(cl) or cl)
            for attr_name in uniq:
                if getattr(cl_fields, attr_name).default is NOTHING:
                    break
            else:
                raise ValueError(f"{cl} has no usable non-default attributes.")
            uniq_attrs_dict[attr_name] = cl
        else:
            fallback = cl

    def dis_func(data: Mapping[Any, Any]) -> Optional[Type]:
        if not isinstance(data, Mapping):
            raise ValueError("Only input mappings are supported.")
        for k, v in uniq_attrs_dict.items():
            if k in data:
                return v
        return fallback

    return dis_func


create_uniq_field_dis_func = create_default_dis_func
