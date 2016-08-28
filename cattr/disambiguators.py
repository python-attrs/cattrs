"""Utilities for union (sum type) disambiguation."""
from functools import reduce
from operator import or_
from typing import Callable, Mapping, Sequence, Type, Union

from attr import fields, NOTHING


def create_uniq_field_dis_func(*cls: Sequence[Type]) -> Callable:
    """Given attr classes, generate a disambiguation function.

    The function is based on unique required fields."""
    if len(cls) < 2:
        raise ValueError('At least two classes required.')
    req_attrs = [set(at.name for at in fields(cl) if at.default is NOTHING)
                 for cl in cls]
    if len([attr_set for attr_set in req_attrs if len(attr_set) == 0]) > 1:
        raise ValueError('At least two classes have no required attributes.')
    # TODO: Deal with a single class having no required attrs.
    # For each class, attempt to generate a single unique required field.
    uniq_attrs_dict = {}
    for cl, cl_reqs in zip(cls, req_attrs):
        other_reqs = reduce(or_, (req_set for req_set in req_attrs
                                  if req_set is not cl_reqs))
        uniq = cl_reqs - other_reqs
        if not uniq:
            raise ValueError('{} has no usable unique attributes.'.format(cl))
        uniq_attrs_dict[next(iter(uniq))] = cl

    def dis_func(data: Mapping) -> Union:
        for k, v in uniq_attrs_dict.items():
            if k in data:
                return v
        raise ValueError('Unable to disambiguate {}.'.format(data))

    return dis_func
