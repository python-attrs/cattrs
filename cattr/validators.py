from typing import Tuple

from attr import attr
from attr.validators import _InstanceOfValidator, optional


class _GenericSequenceValidator(_InstanceOfValidator):
    generic_arg = attr()


def instance_of(type):
    """
    A validator that raises a :exc:`TypeError` if the initializer is called
    with a wrong type for this particular attribute (checks are perfomed using
    :func:`isinstance` therefore it's also valid to pass a tuple of types).

    :param type: The type to check for.
    :type type: type or tuple of types

    The :exc:`TypeError` is raised with a human readable error message, the
    attribute (of type :class:`attr.Attribute`), the expected type, and the
    value it got.
    """
    if type is Tuple:
        # Tuples can't be used with isinstance.
        if type.__tuple_use_ellipsis__:
            return _GenericSequenceValidator(tuple, type.__tuple_params__[0])
        else:
            type = tuple
    return _InstanceOfValidator(type)
