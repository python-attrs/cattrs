import sys
from functools import lru_cache, singledispatch  # noqa
from typing import (
    Dict,
    FrozenSet,
    Mapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Tuple,
)

version_info = sys.version_info[0:3]
is_py36 = version_info[:2] == (3, 6)

unicode = str
bytes = bytes

if not is_py36:
    from typing import List, Union, _GenericAlias, ForwardRef, Any

    def is_union_type(obj):
        return (
            obj is Union
            or isinstance(obj, _GenericAlias)
            and obj.__origin__ is Union
        )

    def is_sequence(type):
        return type is List or (
            type.__class__ is _GenericAlias
            and type.__origin__ is not Union
            and issubclass(type.__origin__, Sequence)
        )

    def is_frozenset(type):
        return type.__class__ is _GenericAlias and issubclass(
            type.__origin__, FrozenSet
        )

    def is_mutable_set(type):
        return type.__class__ is _GenericAlias and issubclass(
            type.__origin__, MutableSet
        )

    def is_tuple(type):
        return type is Tuple or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, Tuple)
        )

    def is_mapping(type):
        return type is Mapping or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, Mapping)
        )

    bare_list_args = List.__args__
    bare_seq_args = Sequence.__args__
    bare_mapping_args = Mapping.__args__
    bare_dict_args = Dict.__args__
    bare_mutable_seq_args = MutableSequence.__args__

    def is_bare(type):
        args = type.__args__
        return (
            args == bare_list_args
            or args == bare_seq_args
            or args == bare_mapping_args
            or args == bare_dict_args
            or args == bare_mutable_seq_args
        )

    @lru_cache(32)
    def _get_class_namespace(class_: type) -> Dict[str, Any]:
        return vars(sys.modules[class_.__module__])

    @lru_cache(32)
    def get_type(parent_class: type, type_: Union[type, str]) -> type:
        """Returns the actual type if type_ is a string."""

        if isinstance(type_, str):
            globalns = _get_class_namespace(parent_class)
            forwardRef = ForwardRef(type_, is_argument=False)
            return forwardRef._evaluate(globalns, None)
        else:
            return type_

else:
    from typing import _Union

    def is_union_type(obj):
        """Return true if the object is a union. """
        return isinstance(obj, _Union)

    def is_frozenset(type):
        return issubclass(type, FrozenSet)

    def is_mutable_set(type):
        return issubclass(type, MutableSet)

    def is_sequence(type):
        is_string = issubclass(type, str)
        return issubclass(type, Sequence) and not is_string

    def is_tuple(type):
        return issubclass(type, Tuple)

    def is_mapping(type):
        return issubclass(type, Mapping)

    def is_bare(type):
        return not type.__args__

    is_bare_frozenset = is_bare

    def get_type(ignored: type, type_: type) -> type:
        return type_
