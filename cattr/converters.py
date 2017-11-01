from enum import Enum
from typing import (List, Mapping, Sequence, Optional, MutableSequence,
                    TypeVar, Any, FrozenSet, MutableSet, Set, MutableMapping,
                    Dict, Tuple, _Union)
from ._compat import lru_cache, unicode, bytes, is_py2
from .disambiguators import create_uniq_field_dis_func
from .metadata import TYPE_METADATA_KEY
from .multistrategy_dispatch import MultiStrategyDispatch

from attr import NOTHING


NoneType = type(None)
T = TypeVar('T')
V = TypeVar('V')


class UnstructureStrategy(Enum):
    """`attrs` classes unstructuring strategies."""
    AS_DICT = "asdict"
    AS_TUPLE = "astuple"


def _is_attrs_class(cls):
    return getattr(cls, "__attrs_attrs__", None) is not None


def _is_union_type(obj):
    """ returns true if the object is an instance of union. """
    return isinstance(obj, _Union)


def _subclass(typ):
    """ a shortcut """
    return (lambda cls: issubclass(cls, typ))


class Converter(object):
    """Converts between structured and unstructured data."""
    __slots__ = ('_dis_func_cache', 'unstructure_func', 'unstructure_attrs',
                 'structure_attrs', '_structure', '_dict_factory',
                 '_union_registry', 'structure_func')

    def __init__(self, dict_factory=dict,
                 unstruct_strat=UnstructureStrategy.AS_DICT):

        # Create a per-instance cache.
        self.unstruct_strat = UnstructureStrategy(unstruct_strat)
        if is_py2:  # in py2, the unstruct_strat property setter is not invoked
            self._unstruct_strat(unstruct_strat)

        self._dis_func_cache = lru_cache()(self._get_dis_func)

        self.unstructure_func = MultiStrategyDispatch(
            self._unstructure_default
        )
        self.unstructure_func.register_cls_list([
            (bytes, self._unstructure_identity),
            (unicode, self._unstructure_identity),
        ])
        self.unstructure_func.register_func_list([
            (_subclass(Mapping), self._unstructure_mapping),
            (_subclass(Sequence), self._unstructure_seq),
            (_subclass(Enum), self._unstructure_enum),
            (_is_attrs_class,
             lambda *args, **kwargs: self.unstructure_attrs(*args, **kwargs)),
        ])

        # Per-instance register of to-attrs converters.
        # Singledispatch dispatches based on the first argument, so we
        # store the function and switch the arguments in self.loads.
        self.structure_func = MultiStrategyDispatch(self._structure_default)
        self.structure_func.register_func_list([
            (_subclass(List), self._structure_list),
            (_subclass(Sequence), self._structure_list),
            (_subclass(MutableSequence), self._structure_list),
            (_subclass(MutableSet), self._structure_set),
            (_subclass(Set), self._structure_set),
            (_subclass(FrozenSet), self._structure_frozenset),
            (_subclass(Dict), self._structure_dict),
            (_subclass(Mapping), self._structure_dict),
            (_subclass(MutableMapping), self._structure_dict),
            (_subclass(Tuple), self._structure_tuple),
            (_is_union_type, self._structure_union),
            (_is_attrs_class,
             lambda *args, **kwargs: self.structure_attrs(*args, **kwargs))
        ])

        # Strings are sequences.
        self.structure_func.register_cls_list([
            (unicode, self._structure_unicode if is_py2
             else self._structure_call),
            (bytes, self._structure_call),
            (int, self._structure_call),
            (float, self._structure_call),
            (Enum, self._structure_call),
        ])
        self._structure = self.structure_func
        self._dict_factory = dict_factory

        # Unions are instances now, not classes. We use different registry.
        self._union_registry = {}

    def unstructure(self, obj):
        return self.unstructure_func.dispatch(type(obj))(obj)

    @property
    def unstruct_strat(self):
        # type: () -> UnstructureStrategy
        """The default way of unstructuring ``attrs`` classes."""
        return (UnstructureStrategy.AS_DICT
                if self.unstructure_attrs == self.unstructure_attrs_asdict
                else UnstructureStrategy.AS_TUPLE)

    @unstruct_strat.setter
    def unstruct_strat(self, val):
        # type: (UnstructureStrategy) -> None
        self._unstruct_strat(val)

    def _unstruct_strat(self, val):
        # type: (UnstructureStrategy) -> None
        if val is UnstructureStrategy.AS_DICT:
            self.unstructure_attrs = self.unstructure_attrs_asdict
            self.structure_attrs = self.structure_attrs_fromdict
        else:
            self.unstructure_attrs = self.unstructure_attrs_astuple
            self.structure_attrs = self.structure_attrs_fromtuple

    def register_unstructure_hook(self, cls, func):
        # type: (Type[T], Callable[[T], Any]) -> None
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        self.unstructure_func.register_cls_list([(cls, func)])

    def register_unstructure_hook_func(self, check_func, func):
        """Register a class-to-primitive converter function for a class, using
        a function to check if it's a match.
        """
        # type: (Callable[Any], Callable[T], Any]) -> None
        self.unstructure_func.register_func_list([(check_func, func)])

    def register_structure_hook(self, cl, func):
        """Register a primitive-to-class converter function for a type.

        The converter function should take two arguments:
          * a Python object to be converted,
          * the type to convert to

        and return the instance of the class. The type may seem redundant, but
        is sometimes needed (for example, when dealing with generic classes).
        """
        # type: (Type[T], Callable[[Any, Type], T) -> None
        if _is_union_type(cl):
            self._union_registry[cl] = func
        else:
            self._structure.register_cls_list([(cl, func)])

    def register_structure_hook_func(self, check_func, func):
        # type: (Callable[Any], Callable[T], Any]) -> None
        """Register a class-to-primitive converter function for a class, using
        a function to check if it's a match.
        """
        self.structure_func.register_func_list([(check_func, func)])

    def structure(self, obj, cl):
        """Convert unstructured Python data structures to structured data."""
        # type: (Any, Type) -> Any
        return self.structure_func.dispatch(cl)(obj, cl)

    # Classes to Python primitives.
    def _unstructure_default(self, obj):
        return obj

    def unstructure_attrs_asdict(self, obj):
        """Our version of `attrs.asdict`, so we can call back to us."""
        attrs = obj.__class__.__attrs_attrs__
        rv = self._dict_factory()
        for a in attrs:
            name = a.name
            v = getattr(obj, name)
            rv[name] = self.unstructure(v)
        return rv

    def unstructure_attrs_astuple(self, obj):
        """Our version of `attrs.astuple`, so we can call back to us."""
        attrs = obj.__class__.__attrs_attrs__
        return tuple(self.unstructure(getattr(obj, a.name)) for a in attrs)

    def _unstructure_enum(self, obj):
        """Convert an enum to its value."""
        return obj.value

    def _unstructure_identity(self, obj):
        """Just pass it through."""
        return obj

    def _unstructure_seq(self, seq):
        """Convert a sequence to primitive equivalents."""
        # We can reuse the sequence class, so tuples stay tuples.
        return seq.__class__(self.unstructure(e) for e in seq)

    def _unstructure_mapping(self, mapping):
        # type: (Mapping) -> Any
        """Convert a mapping of attr classes to primitive equivalents."""

        # We can reuse the mapping class, so dicts stay dicts and OrderedDicts
        # stay OrderedDicts.
        return mapping.__class__((self.unstructure(k), self.unstructure(v))
                                 for k, v in mapping.items())

    # Python primitives to classes.

    def _structure_default(self, obj, cl):
        """This is the fallthrough case. Everything is a subclass of `Any`.

        A special condition here handles ``attrs`` classes.

        Bare optionals end here too (optionals with arguments are unions.) We
        treat bare optionals as Any.
        """
        if cl is Any or cl is Optional:
            return obj
        # We don't know what this is, so we complain loudly.
        msg = "Unsupported type: {0}. Register a structure hook for " \
              "it.".format(cl)
        raise ValueError(msg)

    def _structure_call(self, obj, cl):
        """Just call ``cl`` with the given ``obj``.

        This is just an optimization on the ``_structure_default`` case, when
        we know we can skip the ``if`` s. Use for ``str``, ``bytes``, ``enum``,
        etc.
        """
        return cl(obj)

    def _structure_unicode(self, obj, cl):
        """Just call ``cl`` with the given ``obj``"""
        if not isinstance(obj, (bytes, unicode)):
            return cl(str(obj))
        else:
            return obj

    # Attrs classes.

    def structure_attrs_fromtuple(self, obj, cl):
        # type: (Sequence[Any], Type) -> Any
        """Load an attrs class from a sequence (tuple)."""
        conv_obj = []  # A list of converter parameters.
        for a, value in zip(cl.__attrs_attrs__, obj):
            # We detect the type by the metadata.
            converted = self._structure_attr_from_tuple(a, a.name, value)
            conv_obj.append(converted)

        return cl(*conv_obj)

    def _structure_attr_from_tuple(self, a, name, value):
        """Handle an individual attrs attribute."""
        type_ = a.metadata.get(TYPE_METADATA_KEY)
        if type_ is None:
            # No type metadata.
            return value
        return self._structure.dispatch(type_)(value, type_)

    def structure_attrs_fromdict(self, obj, cl):
        # type: (Mapping, Type) -> Any
        """Instantiate an attrs class from a mapping (dict)."""
        # For public use.
        conv_obj = obj.copy()  # Dict of converted parameters.
        for a in cl.__attrs_attrs__:
            name = a.name
            # We detect the type by metadata.
            converted = self._structure_attr_from_dict(a, name, obj)
            conv_obj[name] = converted

        return cl(**conv_obj)

    def _structure_attr_from_dict(self, a, name, mapping):
        """Handle an individual attrs attribute structuring."""
        type_ = a.metadata.get(TYPE_METADATA_KEY)
        val = mapping.get(name, a.default)
        if type_ is None:
            # No type.
            return val
        if _is_union_type(type_):

            if NoneType in type_.__args__ and val is NOTHING:
                return None
            return self._structure_union(val, type_)
        return self._structure.dispatch(type_)(val, type_)

    def _structure_list(self, obj, cl):
        # type: (Type[GenericMeta], Iterable[T]) -> List[T]
        """Convert an iterable to a potentially generic list."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return [e for e in obj]
        else:
            elem_type = cl.__args__[0]
            return [self._structure.dispatch(elem_type)(e, elem_type)
                    for e in obj]

    def _structure_set(self, obj, cl):
        # type: (Type[GenericMeta], Iterable[T]) -> MutableSet[T]
        """Convert an iterable into a potentially generic set."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return set(obj)
        else:
            elem_type = cl.__args__[0]
            return {self._structure.dispatch(elem_type)(e, elem_type)
                    for e in obj}

    def _structure_frozenset(self, obj, cl):
        # type: (Type[GenericMeta], Iterable[T]) -> FrozenSet[T]
        """Convert an iterable into a potentially generic frozenset."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return frozenset(obj)
        else:
            elem_type = cl.__args__[0]
            return frozenset((self._structure.dispatch(elem_type)(e, elem_type)
                              for e in obj))

    def _structure_dict(self, obj, cl):
        # type: (Type[GenericMeta], Mapping[T, V]) -> Dict[T, V]
        """Convert a mapping into a potentially generic dict."""
        if not cl.__args__ or cl.__args__ == (Any, Any):
            return dict(obj)
        else:
            key_type, val_type = cl.__args__
            if key_type is Any:
                val_conv = self._structure.dispatch(val_type)
                return {k: val_conv(v, val_type) for k, v in obj.items()}
            elif val_type is Any:
                key_conv = self._structure.dispatch(key_type)
                return {key_conv(k, key_type): v for k, v in obj.items()}
            else:
                key_conv = self._structure.dispatch(key_type)
                val_conv = self._structure.dispatch(val_type)
                return {key_conv(k, key_type): val_conv(v, val_type)
                        for k, v in obj.items()}

    def _structure_union(self, obj, union):
        # type: (_Union, Any): -> Any
        """Deal with converting a union."""

        # Note that optionals are unions that contain NoneType. We check for
        # NoneType early and handle the case of obj being None, so
        # disambiguation functions don't need to handle NoneType.

        # Check the union registry first.
        handler = self._union_registry.get(union)
        if handler is not None:
            return handler(obj, union)

        # Unions with NoneType in them are basically optionals.
        union_params = union.__args__
        if NoneType in union_params:
            if obj is None:
                return None
            if len(union_params) == 2:
                # This is just a NoneType and something else.
                other = (union_params[0] if union_params[1] is NoneType
                         else union_params[1])
                # We can't actually have a Union of a Union, so this is safe.
                return self._structure.dispatch(other)(obj, other)

        # Getting here means either this is not an optional, or it's an
        # optional with more than one parameter.
        # Let's support only unions of attr classes for now.
        cl = self._dis_func_cache(union)(obj)
        return self._structure.dispatch(cl)(obj, cl)

    def _structure_tuple(self, obj, tup):
        # type: (Type[Tuple], Iterable) -> Any
        """Deal with converting to a tuple."""
        tup_params = tup.__args__
        has_ellipsis = (tup_params and tup_params[-1] is Ellipsis)
        if tup_params is None or (has_ellipsis and tup_params[0] is Any):
            # Just a Tuple. (No generic information.)
            return tuple(obj)
        if has_ellipsis:
            # We're dealing with a homogenous tuple, Tuple[int, ...]
            tup_type = tup_params[0]
            conv = self._structure.dispatch(tup_type)
            return tuple(conv(e, tup_type) for e in obj)
        else:
            # We're dealing with a heterogenous tuple.
            return tuple(self._structure.dispatch(t)(e, t)
                         for t, e in zip(tup_params, obj))

    def _get_dis_func(self, union):
        # type: (Type) -> Callable[..., Type]
        """Fetch or try creating a disambiguation function for a union."""
        if not all(hasattr(e, '__attrs_attrs__')
                   for e in union.__args__):
            raise ValueError('Only unions of attr classes supported '
                             'currently. Register a loads hook manually.')
        return create_uniq_field_dis_func(*union.__args__)
