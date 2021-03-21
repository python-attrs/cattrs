import sys
from attr import (
    Factory,
    NOTHING,
    fields as attrs_fields,
    Attribute,
)
from dataclasses import (
    MISSING,
    is_dataclass,
    fields as dataclass_fields,
)
from typing import (
    Any,
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


def has(cls):
    return hasattr(cls, "__attrs_attrs__") or hasattr(
        cls, "__dataclass_fields__"
    )


def fields(type):
    try:
        return type.__attrs_attrs__
    except AttributeError:
        try:
            return dataclass_fields(type)
        except AttributeError:
            raise Exception("Not an attrs or dataclass class.")


def adapted_fields(type) -> List[Attribute]:
    """Return the attrs format of `fields()` for attrs and dataclasses."""
    if is_dataclass(type):
        return [
            Attribute(
                attr.name,
                attr.default
                if attr.default is not MISSING
                else (
                    Factory(attr.default_factory)
                    if attr.default_factory is not MISSING
                    else NOTHING
                ),
                None,
                True,
                None,
                True,
                attr.init,
                True,
                type=attr.type,
            )
            for attr in dataclass_fields(type)
        ]
    else:
        return attrs_fields(type)


if is_py37 or is_py38:
    from typing import Union, _GenericAlias

    def is_annotated(_):
        return False

    def is_tuple(type):
        return type in (Tuple, tuple) or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, Tuple)
        )

    def is_union_type(obj):
        return (
            obj is Union
            or isinstance(obj, _GenericAlias)
            and obj.__origin__ is Union
        )

    def is_sequence(type: Any) -> bool:
        return type in (List, list, Tuple, tuple) or (
            type.__class__ is _GenericAlias
            and type.__origin__ is not Union
            and issubclass(type.__origin__, Sequence)
        )

    def is_mutable_set(type):
        return type is set or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, MutableSet)
        )

    def is_frozenset(type):
        return type is frozenset or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, FrozenSet)
        )

    def is_mapping(type):
        return type in (Mapping, dict) or (
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
        _AnnotatedAlias,
    )
    from collections.abc import (
        MutableSequence as AbcMutableSequence,
        Sequence as AbcSequence,
        MutableSet as AbcMutableSet,
        Set as AbcSet,
    )

    def is_annotated(type) -> bool:
        return getattr(type, "__class__", None) is _AnnotatedAlias

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

    def is_sequence(type: Any) -> bool:
        origin = getattr(type, "__origin__", None)
        return (
            type
            in (
                List,
                list,
                Sequence,
                MutableSequence,
                AbcMutableSequence,
                tuple,
            )
            or (
                type.__class__ is _GenericAlias
                and (
                    (origin is not tuple)
                    and issubclass(
                        origin,
                        Sequence,
                    )
                    or origin is tuple
                    and type.__args__[1] is ...
                )
            )
            or (origin in (list, AbcMutableSequence, AbcSequence))
            or (origin is tuple and type.__args__[1] is ...)
        )

    def is_mutable_set(type):
        return (
            type in (Set, MutableSet, set)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, MutableSet)
            )
            or (
                getattr(type, "__origin__", None)
                in (set, AbcMutableSet, AbcSet)
            )
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
