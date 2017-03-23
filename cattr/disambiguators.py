"""Utilities for union (sum type) disambiguation."""
from collections import OrderedDict
from functools import reduce
from operator import or_
from ._compat import Callable, Mapping, Sequence, Type, Union

from attr import fields, NOTHING


def create_uniq_field_dis_func(*cls):
    """Given attr classes, generate a disambiguation function.

    The function is based on unique required fields."""
    # type: (*Sequence[Type]) -> Callable
    if len(cls) < 2:
        raise ValueError('At least two classes required.')
    cls_and_req_attrs = [(cl, set(at.name for at in fields(cl)
                         if at.default is NOTHING)) for cl in cls]
    if len([attrs for _, attrs in cls_and_req_attrs if len(attrs) == 0]) > 1:
        raise ValueError('At least two classes have no required attributes.')
    # TODO: Deal with a single class having no required attrs.
    # For each class, attempt to generate a single unique required field.
    uniq_attrs_dict = OrderedDict()
    cls_and_req_attrs.sort(key=lambda c_a: -len(c_a[1]))

    fallback = None  # If none match, try this.

    for i, (cl, cl_reqs) in enumerate(cls_and_req_attrs):
        other_classes = cls_and_req_attrs[i+1:]
        if other_classes:
            other_reqs = reduce(or_, (c_a[1] for c_a in other_classes))
            uniq = cl_reqs - other_reqs
            if not uniq:
                raise ValueError('{} has no usable unique attributes.'.format(cl))
            uniq_attrs_dict[next(iter(uniq))] = cl
        else:
            if fallback is not None:
                raise ValueError("Can't disambiguate between "
                                 "{} and {}.".format(fallback, cl))
            fallback = cl

    def dis_func(data):
        # type: (Mapping) -> Union
        for k, v in uniq_attrs_dict.items():
            if k in data:
                return v
        if fallback is not None:
            return fallback
        raise ValueError('Unable to disambiguate {}.'.format(data))

    return dis_func
