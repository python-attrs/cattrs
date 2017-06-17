from enum import unique, Enum
from ._compat import lru_cache, singledispatch
from ._compat import (Callable, List, Mapping, Sequence, Type, Union, Optional,
                      GenericMeta, MutableSequence, TypeVar, Any, FrozenSet,
                      MutableSet, Set, MutableMapping, Dict, Tuple, Iterable,
                      _Union)
from ._compat import unicode, bytes, is_py2
from .metadata import TYPE_METADATA_KEY

from attr import NOTHING
from attr.validators import _InstanceOfValidator, _OptionalValidator

from .disambiguators import create_uniq_field_dis_func

NoneType = type(None)
T = TypeVar('T')
V = TypeVar('V')


@unique
class UnstructureStrategy(Enum):
    """`attrs` classes unstructuring strategies."""
    AS_DICT = "asdict"
    AS_TUPLE = "astuple"


class Converter(object):
    """Converts between structured and unstructured data."""
    def __init__(self, dict_factory=dict,
                 unstruct_strat=UnstructureStrategy.AS_DICT  # type: UnstructureStrategy
                 ):

        # Create a per-instance cache.
        self.unstruct_strat = UnstructureStrategy(unstruct_strat)
        if is_py2:  # in py2, the unstruct_strat property setter is not invoked here
            self._unstruct_strat(unstruct_strat)

        self._get_dis_func = lru_cache()(self._get_dis_func)

        # Per-instance register of to-Python converters.
        unstructure = singledispatch(self._unstructure)
        unstructure.register(Enum, self._unstructure_enum)
        unstructure.register(unicode, self._unstructure_identity)
        unstructure.register(bytes, self._unstructure_identity)
        unstructure.register(Sequence, self._unstructure_seq)
        unstructure.register(Mapping, self._unstructure_mapping)

        self.unstructure = unstructure

        # Per-instance register of to-attrs converters.
        # Singledispatch dispatches based on the first argument, so we
        # store the function and switch the arguments in self.loads.
        structure = singledispatch(self._structure_default)
        structure.register(Any, self._structure_default)  # Bare opts here too.
        structure.register(List, self._structure_list)
        structure.register(Sequence, self._structure_list)
        structure.register(MutableSequence, self._structure_list)
        structure.register(MutableSet, self._structure_set)
        structure.register(Set, self._structure_set)
        structure.register(FrozenSet, self._structure_frozenset)
        structure.register(Dict, self._structure_dict)
        structure.register(Mapping, self._structure_dict)
        structure.register(MutableMapping, self._structure_dict)
        structure.register(Tuple, self._structure_tuple)
        structure.register(_Union, self._structure_union)
        if is_py2:
            # handle unicode with care in python2
            structure.register(unicode, self._structure_unicode)
        else:
            structure.register(unicode, self._structure_call)  # Strings are sequences.
        structure.register(bytes, self._structure_call)  # Bytes are sequences.
        structure.register(int, self._structure_call)
        structure.register(float, self._structure_call)
        structure.register(Enum, self._structure_call)

        self.structure_attrs = self.structure_attrs_fromdict
        self._structure = structure
        self._dict_factory = dict_factory
        # Unions are instances now, not classes. We use different registry.
        self._union_registry = {}

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
        else:
            self.unstructure_attrs = self.unstructure_attrs_astuple

    def register_unstructure_hook(self, cls, func):
        # type: (Type[T], Callable[[T], Any]) -> None
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        self.unstructure.register(cls, func)

    def register_structure_hook(self, cl, func):
        """Register a primitive-to-class converter function for a type.

        The converter function should take two arguments:
          * a Python object to be converted,
          * the type to convert to

        and return the instance of the class. The type may seem redundant, but
        is sometimes needed (for example, when dealing with generic classes).
        """
        # type: (Type[T], Callable[[Any, Type], T) -> None
        if isinstance(cl, _Union):
            self._union_registry[cl] = func
        else:
            self._structure.register(cl, lambda t, o: func(o, t))

    def structure(self, obj, cl):
        """Convert unstructured Python data structures to structured data."""
        # type: (Any, Type) -> Any

        # Unions aren't classes, but rather instances of typing._Union now.
        return (self._structure.dispatch(cl)(cl, obj)
                if not isinstance(cl, _Union)
                else self._structure_union(cl, obj))  # For Unions.

    # Classes to Python primitives.

    def _unstructure(self, obj):
        """Convert given attrs classes to their primitive equivalents.

        Other classes are passed through unchanged.
        """
        return (self.unstructure_attrs(obj)
                if getattr(obj.__class__, "__attrs_attrs__", None) is not None
                else obj)

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

    def _structure_default(self, cl, obj):
        """This is the fallthrough case. Everything is a subclass of `Any`.

        A special condition here handles ``attrs`` classes.

        Bare optionals end here too (optionals with arguments are unions.) We
        treat bare optionals as Any.
        """
        if cl is Any or cl is Optional:
            return obj
        if hasattr(cl, '__attrs_attrs__'):
            # This is an attrs class
            return self.structure_attrs(obj, cl)
        # We don't know what this is, so we complain loudly.
        msg = "Unsupported type: {0}. Register a structure hook for " \
              "it.".format(cl)
        raise ValueError(msg)

    def _structure_call(self, cl, obj):
        """Just call ``cl`` with the given ``obj``.

        This is just an optimization on the ``_structure_default`` case, when
        we know we can skip the ``if`` s. Use for ``str``, ``bytes``, ``enum``,
        etc.
        """
        return cl(obj)

    def _structure_unicode(self, cl, obj):
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
            converted = self._handle_attr_attribute(a, a.name, value)
            conv_obj.append(converted)

        return cl(*conv_obj)

    def _handle_attr_attribute(self, a, name, value):
        """Handle an individual attrs attribute."""
        type_ = a.metadata.get(TYPE_METADATA_KEY)
        if type_ is None:
            # No type metadata.
            return value
        if isinstance(type_, _Union):
            # This is a union.
            return self._structure_union(type_, value)
        return self._structure.dispatch(type_)(type_, value)

    def structure_attrs_fromdict(self, obj, cl):
        # type: (Mapping, Type) -> Any
        """Instantiate an attrs class from a mapping (dict)."""
        # For public use.
        conv_obj = obj.copy()  # Dict of converted parameters.
        for a in cl.__attrs_attrs__:
            name = a.name
            # We detect the type by metadata.
            converted = self._handle_attr_mapping_attribute(a, name, obj)
            if converted is NOTHING:
                continue
            conv_obj[name] = converted

        return cl(**conv_obj)

    def _handle_attr_mapping_attribute(self, a, name, mapping):
        """Handle an individual attrs attribute structuring."""
        type_ = a.metadata.get(TYPE_METADATA_KEY)
        if type_ is None:
            # No type.
            return mapping[name]
        if isinstance(type_, _Union):
            # This is a union.
            val = mapping.get(name, NOTHING)
            if NoneType in type_.__args__ and val is NOTHING:
                return NOTHING
            return self._structure_union(type_, val)
        return self._structure.dispatch(type_)(type_, mapping.get(a.name))

    def _structure_list(self, cl, obj):
        # type: (Type[GenericMeta], Iterable[T]) -> List[T]
        """Convert an iterable to a potentially generic list."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return [e for e in obj]
        else:
            elem_type = cl.__args__[0]
            conv = (self._structure.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._structure_union)
            return [conv(elem_type, e) for e in obj]

    def _structure_set(self, cl, obj):
        # type: (Type[GenericMeta], Iterable[T]) -> MutableSet[T]
        """Convert an iterable into a potentially generic set."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return set(obj)
        else:
            elem_type = cl.__args__[0]
            conv = (self._structure.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._structure_union)
            return {conv(elem_type, e) for e in obj}

    def _structure_frozenset(self, cl, obj):
        # type: (Type[GenericMeta], Iterable[T]) -> FrozenSet[T]
        """Convert an iterable into a potentially generic frozenset."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return frozenset(obj)
        else:
            elem_type = cl.__args__[0]
            conv = (self._structure.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._structure_union)
            return frozenset([conv(elem_type, e) for e in obj])

    def _structure_dict(self, cl, obj):
        # type: (Type[GenericMeta], Mapping[T, V]) -> Dict[T, V]
        """Convert a mapping into a potentially generic dict."""
        if not cl.__args__ or cl.__args__ == (Any, Any):
            return dict(obj)
        else:
            key_type, val_type = cl.__args__
            if key_type is Any:
                val_conv = (self._structure.dispatch(val_type)
                            if not isinstance(val_type, _Union)
                            else self._structure_union)
                return {k: val_conv(val_type, v) for k, v in obj.items()}
            elif val_type is Any:
                key_conv = (self._structure.dispatch(key_type)
                            if not isinstance(key_type, _Union)
                            else self._structure_union)
                return {key_conv(key_type, k): v for k, v in obj.items()}
            else:
                key_conv = (self._structure.dispatch(key_type)
                            if not isinstance(key_type, _Union)
                            else self._structure_union)
                val_conv = (self._structure.dispatch(val_type)
                            if not isinstance(val_type, _Union)
                            else self._structure_union)
                return {key_conv(key_type, k): val_conv(val_type, v)
                        for k, v in obj.items()}

    def _structure_union(self, union, obj):
        # type: (_Union, Any): -> Any
        """Deal with converting a union."""

        # Note that optionals are unions that contain NoneType. We check for
        # NoneType early and handle the case of obj being None, so
        # disambiguation functions don't need to handle NoneType.

        # Check the union registry first.
        handler = self._union_registry.get(union)
        if handler is not None:
            return handler(union, obj)

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
                return self._structure.dispatch(other)(other, obj)

        # Getting here means either this is not an optional, or it's an
        # optional with more than one parameter.
        # Let's support only unions of attr classes for now.
        cl = self._get_dis_func(union)(obj)
        return self._structure.dispatch(cl)(cl, obj)

    def _structure_tuple(self, tup, obj):
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
            conv = (self._structure.dispatch(tup_type)
                    if not isinstance(tup_type, _Union)
                    else self._structure_union)
            return tuple(conv(tup_type, e) for e in obj)
        else:
            # We're dealing with a heterogenous tuple.
            return tuple(self._structure.dispatch(t)(t, e)
                         if not isinstance(t, _Union)
                         else self._structure_union(t, e)
                         for t, e in zip(tup_params, obj))

    def _get_dis_func(self, union):
        # type: (Type) -> Callable[..., Type]
        """Fetch or try creating a disambiguation function for a union."""
        if not all(hasattr(e, '__attrs_attrs__')
                   for e in union.__args__):
            raise ValueError('Only unions of attr classes supported '
                             'currently. Register a loads hook manually.')
        return create_uniq_field_dis_func(*union.__args__)
