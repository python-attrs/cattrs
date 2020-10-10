import sys
from functools import lru_cache, singledispatch  # noqa
from typing import (
    Dict,
    FrozenSet,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
    Tuple,
)

version_info = sys.version_info[0:3]
is_py37 = version_info[:2] == (3, 7)
is_py38 = version_info[:2] == (3, 8)
is_py39_plus = version_info[:2] >= (3, 9)

if is_py37:

    def get_args(cl):
        return cl.__args__

    def get_origin(cl):
        return getattr(cl, "__origin__", None)


else:
    from typing import get_args, get_origin  # NOQA


if is_py37 or is_py38:
    from typing import Union, _GenericAlias

    def is_tuple(type):
        return type is Tuple or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, Tuple)
        )

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

    def is_mutable_set(type):
        return type.__class__ is _GenericAlias and issubclass(
            type.__origin__, MutableSet
        )

    def is_frozenset(type):
        return type.__class__ is _GenericAlias and issubclass(
            type.__origin__, FrozenSet
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


else:
    # 3.9+
    from typing import (
        Union,
        _GenericAlias,
        _SpecialGenericAlias,
        _UnionGenericAlias,
    )

    def is_tuple(type):
        return (
            type in (Tuple, tuple)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, Tuple)
            )
            or (getattr(type, "__origin__", None) is tuple)
        )

    def is_union_type(obj):
        return (
            obj is Union
            or isinstance(obj, _UnionGenericAlias)
            and obj.__origin__ is Union
        )

    def is_sequence(type):
        return (
            type in (List, list, Sequence, MutableSequence)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, Sequence)
            )
            or (getattr(type, "__origin__", None) is list)
        )

    def is_mutable_set(type):
        return (
            type in (Set, MutableSet, set)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, MutableSet)
            )
            or (getattr(type, "__origin__", None) is set)
        )

    def is_frozenset(type):
        return (
            type in (FrozenSet, frozenset)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, FrozenSet)
            )
            or (getattr(type, "__origin__", None) is frozenset)
        )

    def is_bare(type):
        return isinstance(type, _SpecialGenericAlias) or (
            not hasattr(type, "__origin__") and not hasattr(type, "__args__")
        )

    def is_mapping(type):
        return (
            type in (Mapping, Dict, MutableMapping, dict)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, Mapping)
            )
            or (getattr(type, "__origin__", None) is dict)
        )


def is_generic(obj):
    return isinstance(obj, _GenericAlias)
