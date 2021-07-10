import sys
from dataclasses import MISSING
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from typing import Any, Dict, FrozenSet, List
from typing import Mapping as TypingMapping
from typing import MutableMapping as TypingMutableMapping
from typing import MutableSequence as TypingMutableSequence
from typing import MutableSet as TypingMutableSet
from typing import Sequence as TypingSequence
from typing import Set as TypingSet
from typing import Tuple

from attr import NOTHING, Attribute, Factory
from attr import fields as attrs_fields

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


def has_with_generic(cls):
    """Test whether the class if a normal or generic attrs or dataclass."""
    return has(cls) or has(get_origin(cls))


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


def is_hetero_tuple(type: Any) -> bool:
    origin = getattr(type, "__origin__", None)
    return origin is tuple and ... not in type.__args__


if is_py37 or is_py38:
    Set = TypingSet
    MutableSet = TypingMutableSet
    Sequence = TypingSequence
    MutableSequence = TypingMutableSequence
    MutableMapping = TypingMutableMapping
    Mapping = TypingMapping
    FrozenSetSubscriptable = FrozenSet
    TupleSubscriptable = Tuple

    from collections import Counter as ColCounter
    from typing import Counter, Union, _GenericAlias

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
            and (
                type.__origin__ not in (Union, Tuple, tuple)
                and issubclass(type.__origin__, TypingSequence)
            )
            or (type.__origin__ in (Tuple, tuple) and type.__args__[1] is ...)
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
        return type in (TypingMapping, dict) or (
            type.__class__ is _GenericAlias
            and issubclass(type.__origin__, TypingMapping)
        )

    bare_list_args = List.__args__
    bare_seq_args = TypingSequence.__args__
    bare_mapping_args = TypingMapping.__args__
    bare_dict_args = Dict.__args__
    bare_mutable_seq_args = TypingMutableSequence.__args__

    def is_bare(type):
        args = type.__args__
        return (
            args == bare_list_args
            or args == bare_seq_args
            or args == bare_mapping_args
            or args == bare_dict_args
            or args == bare_mutable_seq_args
        )

    def is_counter(type):
        return (
            type in (Counter, ColCounter)
            or getattr(type, "__origin__", None) is ColCounter
        )

    if is_py38:
        from typing import Literal

        def is_literal(type) -> bool:
            return (
                type.__class__ is _GenericAlias and type.__origin__ is Literal
            )

    else:
        # No literals in 3.7.
        def is_literal(_) -> bool:
            return False


else:
    # 3.9+
    from collections import Counter
    from collections.abc import Mapping as AbcMapping
    from collections.abc import MutableMapping as AbcMutableMapping
    from collections.abc import MutableSequence as AbcMutableSequence
    from collections.abc import MutableSet as AbcMutableSet
    from collections.abc import Sequence as AbcSequence
    from collections.abc import Set as AbcSet
    from typing import Counter as TypingCounter
    from typing import (
        Union,
        _AnnotatedAlias,
        _GenericAlias,
        _SpecialGenericAlias,
        _UnionGenericAlias,
    )

    try:
        # Not present on 3.9.0, so we try carefully.
        from typing import _LiteralGenericAlias

        def is_literal(type) -> bool:
            return type.__class__ is _LiteralGenericAlias

    except ImportError:

        def is_literal(_) -> bool:
            return False

    Set = AbcSet
    MutableSet = AbcMutableSet
    Sequence = AbcSequence
    MutableSequence = AbcMutableSequence
    MutableMapping = AbcMutableMapping
    Mapping = AbcMapping
    FrozenSetSubscriptable = frozenset
    TupleSubscriptable = tuple

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
                TypingSequence,
                TypingMutableSequence,
                AbcMutableSequence,
                tuple,
            )
            or (
                type.__class__ is _GenericAlias
                and (
                    (origin is not tuple)
                    and issubclass(origin, TypingSequence)
                    or origin is tuple
                    and type.__args__[1] is ...
                )
            )
            or (origin in (list, AbcMutableSequence, AbcSequence))
            or (origin is tuple and type.__args__[1] is ...)
        )

    def is_mutable_set(type):
        return (
            type in (TypingSet, TypingMutableSet, set)
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, TypingMutableSet)
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
            type
            in (
                TypingMapping,
                Dict,
                TypingMutableMapping,
                dict,
                AbcMutableMapping,
            )
            or (
                type.__class__ is _GenericAlias
                and issubclass(type.__origin__, TypingMapping)
            )
            or (
                getattr(type, "__origin__", None)
                in (dict, AbcMutableMapping, AbcMapping)
            )
            or issubclass(type, dict)
        )

    def is_counter(type):
        return (
            type in (Counter, TypingCounter)
            or getattr(type, "__origin__", None) is Counter
        )


def is_generic(obj):
    return isinstance(obj, _GenericAlias)


def is_generic_attrs(type):
    return is_generic(type) and has(type.__origin__)
