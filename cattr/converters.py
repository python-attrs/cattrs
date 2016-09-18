from enum import Enum
from functools import lru_cache
from typing import (Callable, List, Mapping, Sequence, Type, Union, Optional,
                    GenericMeta, MutableSequence, TypeVar, Any, FrozenSet,
                    MutableSet, Set, MutableMapping, Dict, Tuple, Iterable)

from attr import NOTHING
from attr.validators import _InstanceOfValidator, _OptionalValidator

from .disambiguators import create_uniq_field_dis_func

try:
    from functools import singledispatch
except ImportError:
    # We use a backport for 3.3.
    from singledispatch import singledispatch

NoneType = type(None)
T = TypeVar('T')
V = TypeVar('V')


class Converter(object):
    """Converts between attrs and Python primitives."""
    def __init__(self, dict_factory=dict):
        # Create a per-instance cache.
        self._get_dis_func = lru_cache()(self._get_dis_func)

        # Per-instance register of to-Python converters.
        dumps = singledispatch(self._dumps)
        dumps.register(Enum, self._dumps_enum)
        dumps.register(str, self._dumps_identity)
        dumps.register(bytes, self._dumps_identity)
        dumps.register(Sequence, self._dumps_seq)
        dumps.register(Mapping, self._dumps_mapping)

        self.dumps = dumps

        # Per-instance register of to-attrs converters.
        # Singledispatch dispatches based on the first argument, so we
        # store the function and switch the arguments in self.loads.
        loads = singledispatch(self._loads_default)
        loads.register(Any, self._loads_default)  # Bare optionals go here too.
        loads.register(List, self._loads_list)
        loads.register(Sequence, self._loads_list)
        loads.register(MutableSequence, self._loads_list)
        loads.register(MutableSet, self._loads_set)
        loads.register(Set, self._loads_set)
        loads.register(FrozenSet, self._loads_frozenset)
        loads.register(Dict, self._loads_dict)
        loads.register(Mapping, self._loads_dict)
        loads.register(MutableMapping, self._loads_dict)
        loads.register(Tuple, self._loads_tuple)
        loads.register(Union, self._loads_union)
        loads.register(str, self._loads_call)  # Strings are sequences.
        loads.register(bytes, self._loads_call)  # Bytes are sequences.
        loads.register(int, self._loads_call)
        loads.register(float, self._loads_call)
        loads.register(Enum, self._loads_call)

        self._loads = loads
        self._dict_factory = dict_factory

    def register_dumps_hook(self, cls: Type[T], func: Callable[[T], Any]):
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        self.dumps.register(cls, func)

    def register_loads_hook(self, cls: Type[T],
                            func: Callable[[Type, Any], T]) -> None:
        """Register a primitive-to-class converter function for a type.

        The converter function should take an instance of a Python primitive
        and return the instance of the class.
        """
        self._loads.register(cls, func)

    def loads(self, obj, cl: Type):
        """Convert unstructured Python data structures to structured data."""
        return self._loads.dispatch(cl)(cl, obj)

    # Classes to Python primitives.

    def _dumps(self, obj):
        """Convert given attrs classes to their primitive equivalents."""
        return (self._dumps_attrs(obj)
                if getattr(obj.__class__, "__attrs_attrs__", None) is not None
                else obj)

    def _dumps_attrs(self, obj):
        """Our version of `attrs.asdict`, so we can call back to us."""
        attrs = obj.__class__.__attrs_attrs__
        rv = self._dict_factory()
        for a in attrs:
            v = getattr(obj, a.name)
            rv[a.name] = self.dumps(v)
        return rv

    def _dumps_enum(self, obj):
        """Convert an enum to its value."""
        return obj.value

    def _dumps_identity(self, obj):
        """Just pass it through."""
        return obj

    def _dumps_seq(self, seq):
        """Convert a sequence to primitive equivalents."""
        # We can reuse the sequence class, so tuples stay tuples.
        return seq.__class__(self.dumps(e) for e in seq)

    def _dumps_mapping(self, mapping: Mapping):
        """Convert a mapping of attr classes to primitive equivalents."""
        # We can reuse the mapping class, so dicts stay dicts and OrderedDicts
        # stay OrderedDicts.
        return mapping.__class__((self.dumps(k), self.dumps(v))
                                 for k, v in mapping.items())

    # Python primitives to classes.

    def _loads_default(self, cl, obj):
        """This is the fallthrough case. Everything is a subclass of `Any`.

        A special condition here handles ``attrs`` classes.

        Bare optionals end here too (optionals with arguments are unions.) We
        treat bare optionals as Any.
        """
        if cl is Any or cl is Optional:
            return obj
        if hasattr(cl, '__attrs_attrs__'):
            # This is an attrs class
            return self._loads_attrs(cl, obj)
        # We don't know what this is. Just try instantiating it.
        # This covers the basics: bools, ints, floats, strings, bytes, enums.
        return cl(obj)

    def _loads_call(self, cl, obj):
        """Just call ``cl`` with the given ``obj``.

        This is just an optimization on the ``_loads_default`` case, when we
        know we can skip the ``if`` s. Use for ``str``, ``bytes``, ``enum``,
        etc.
        """
        return cl(obj)

    def _loads_attrs(self, cl, obj):
        """Handle actual attrs classes."""
        conv_obj = obj.copy()  # Dict of converted parameters.
        for a in cl.__attrs_attrs__:
            name = a.name
            # We detect the type by the validator.
            validator = a.validator
            converted = self._handle_attr_attribute(name, validator, obj)
            if converted is NOTHING:
                continue
            conv_obj[name] = converted

        return cl(**conv_obj)

    def _handle_attr_attribute(self, name, val, mapping):
        """Handle an individual validator attrs validator."""
        if val is None:
            # No validator.
            return mapping[name]
        elif isinstance(val, _OptionalValidator):
            # This is an Optional[something]
            if name not in mapping or mapping[name] is None:
                return NOTHING
            return self._handle_attr_attribute(name, val.validator, mapping)
        elif isinstance(val, _InstanceOfValidator):
            type_ = val.type
            return self._loads.dispatch(type_)(type_, mapping.get(name))
        else:
            return mapping[name]

    def _loads_list(self, cl: Type[GenericMeta], obj: Iterable[T]) -> List[T]:
        """Convert an iterable to a potentially generic list."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return [e for e in obj]
        else:
            elem_type = cl.__args__[0]
            conv = self._loads.dispatch(elem_type)
            return [conv(elem_type, e) for e in obj]

    def _loads_set(self, cl: Type[GenericMeta], obj: Iterable[T])\
            -> MutableSet[T]:
        """Convert an iterable into a potentially generic set."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return set(obj)
        else:
            elem_type = cl.__args__[0]
            conv = self._loads.dispatch(elem_type)
            return {conv(elem_type, e) for e in obj}

    def _loads_frozenset(self, cl: Type[GenericMeta], obj: Iterable[T])\
            -> FrozenSet[T]:
        """Convert an iterable into a potentially generic frozenset."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return frozenset(obj)
        else:
            elem_type = cl.__args__[0]
            conv = self._loads.dispatch(elem_type)
            return frozenset([conv(elem_type, e) for e in obj])

    def _loads_dict(self, cl: Type[GenericMeta], obj: Mapping[T, V])\
            -> Dict[T, V]:
        """Convert a mapping into a potentially generic dict."""
        if not cl.__args__ or cl.__args__ == (Any, Any):
            return dict(obj)
        else:
            key_type, val_type = cl.__args__
            if key_type is Any:
                val_conv = self._loads.dispatch(val_type)
                return {k: val_conv(val_type, v) for k, v in obj.items()}
            elif val_type is Any:
                key_conv = self._loads.dispatch(key_type)
                return {key_conv(key_type, k): v for k, v in obj.items()}
            else:
                key_conv = self._loads.dispatch(key_type)
                val_conv = self._loads.dispatch(val_type)
                return {key_conv(key_type, k): val_conv(val_type, v)
                        for k, v in obj.items()}

    def _loads_union(self, union: Type[Union], obj: Union):
        """Deal with converting a union.

        Note that optionals are unions that contain NoneType. We check for
        NoneType early and handle the case of obj being None, so
        disambiguation functions don't need to handle NoneType.
        """
        # Unions with NoneType in them are basically optionals.
        union_params = union.__union_params__
        if NoneType in union_params:
            if obj is None:
                return None
            if len(union_params) == 2:
                # This is just a NoneType and something else.
                other = (union_params[0] if union_params[1] is NoneType
                         else union_params[1])
                return self._loads.dispatch(other)(other, obj)

        # Getting here means either this is not an optional, or it's an
        # optional with more than one parameter.
        # Let's support only unions of attr classes for now.
        cl = self._get_dis_func(union)(obj)
        return self._loads.dispatch(cl)(cl, obj)

    def _loads_tuple(self, tup: Type[Tuple], obj: Iterable):
        """Deal with converting to a tuple."""
        tup_params = tup.__tuple_params__
        has_ellipsis = tup.__tuple_use_ellipsis__
        if tup_params is None or (has_ellipsis and tup_params[0] is Any):
            # Just a Tuple. (No generic information.)
            return tuple(obj)
        if tup.__tuple_use_ellipsis__:
            # We're dealing with a homogenous tuple, Tuple[int, ...]
            tup_type = tup_params[0]
            conv = self._loads.dispatch(tup_type)
            return tuple(conv(tup_type, e) for e in obj)
        else:
            # We're dealing with a heterogenous tuple.
            return tuple(self._loads.dispatch(t)(t, e)
                         for t, e in zip(tup_params, obj))


    def _get_dis_func(self, union: Type[Union]) -> Callable[..., Type]:
        """Fetch or try creating a disambiguation function for a union."""
        if not all(hasattr(e, '__attrs_attrs__')
                   for e in union.__union_params__):
            raise ValueError('Only unions of attr classes supported '
                             'currently.')
        return create_uniq_field_dis_func(*union.__union_params__)
