from enum import Enum
from functools import lru_cache
from typing import (Callable, List, Mapping, Sequence, Type, Union, UnionMeta,
                    GenericMeta, MutableSequence, TypeVar, Any)

from attr import NOTHING
from attr.validators import _InstanceOfValidator, _OptionalValidator

from .disambiguators import create_uniq_field_dis_func

try:
    from functools import singledispatch
except ImportError:
    # We use a backport for 3.3.
    from singledispatch import singledispatch

T = TypeVar('T')


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
        loads = singledispatch(self._loads)
        loads.register(GenericMeta, self._loads_generic_meta)
        loads.register(UnionMeta, self._loads_union)

        self._loads = loads
        self._dict_factory = dict_factory

    def register_dumps_hook(self, cls: Type[T], func: Callable[[T], Any]):
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        self.dumps.register(cls, func)

    def register_loads_hook(self, cls: Type[T], func: Callable[[Any], T]):
        """Register a primitive-to-class converter function for a type.

        The converter function should take an instance of a Python primitive
        and return the instance of the class.
        """
        self._loads.register(cls, func)

    def loads(self, obj, cl: Type):
        """Convert unstructured Python data structures to structured data."""
        return self._loads(cl, obj)

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

    def _loads(self, cl, obj):
        """Things we can't recognize by isinstance."""
        if hasattr(cl, '__attrs_attrs__'):
            # This is an attrs class
            return self._loads_attrs(cl, obj)
        # We don't know what this is. Just try instantiating it.
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
            return self._loads(type_, mapping.get(name))
        else:
            return mapping[name]

    def _loads_generic_meta(self, cl: Type[GenericMeta], obj):
        """Deal with converting a generic.

        From typing, this could be:
        * Sequence
        * MutableSequence
        * List
        * MutableSet
        * Set
        * FrozenSet
        * Mapping
        * MutableMapping
        * Dict
        """
        origin = cl.__origin__ or cl
        if origin is List or origin is Sequence or origin is MutableSequence:
            # Dealing with a list.
            if not cl.__args__:
                return obj
            else:
                return [self._loads(cl.__args__[0], e) for e in obj]
        else:
            raise ValueError("Unsupported generic type.")

    def _loads_union(self, union: Type[Union], obj: Union):
        """Deal with converting a union."""
        # Let's support only unions of attr classes for now.
        return self._loads(self._get_dis_func(union)(obj), obj)

    def _get_dis_func(self, union: Type[Union]) -> Callable[..., Type]:
        """Fetch or try creating a disambiguation function for a union."""
        if not all(hasattr(e, '__attrs_attrs__')
                   for e in union.__union_params__):
            raise ValueError('Only unions of attr classes supported '
                             'currently.')
        return create_uniq_field_dis_func(*union.__union_params__)
