from enum import unique, Enum
from functools import lru_cache, singledispatch
from ._compat import (Callable, List, Mapping, Sequence, Type, Union, Optional,
                      GenericMeta, MutableSequence, TypeVar, Any, FrozenSet,
                      MutableSet, Set, MutableMapping, Dict, Tuple, Iterable,
                      _Union)

from attr import NOTHING
from attr.validators import _InstanceOfValidator, _OptionalValidator

from .disambiguators import create_uniq_field_dis_func

NoneType = type(None)
T = TypeVar('T')
V = TypeVar('V')


@unique
class AttrsDumpingStrategy(str, Enum):
    """`attrs` classes dumping strategies."""
    AS_DICT = "asdict"
    AS_TUPLE = "astuple"


DumpStratType = Union[str, AttrsDumpingStrategy]


class Converter:
    """Converts between structured and unstructured data."""
    def __init__(self, *, dict_factory=dict,
                 dumping_strat: DumpStratType=AttrsDumpingStrategy.AS_DICT):
        # Create a per-instance cache.
        self.dumping_strat = AttrsDumpingStrategy(dumping_strat)
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
        loads.register(tuple, self._loads_tuple)
        loads.register(_Union, self._loads_union)
        loads.register(str, self._loads_call)  # Strings are sequences.
        loads.register(bytes, self._loads_call)  # Bytes are sequences.
        loads.register(int, self._loads_call)
        loads.register(float, self._loads_call)
        loads.register(Enum, self._loads_call)

        self.loads_attrs = self.loads_attrs_fromdict
        self._loads = loads
        self._dict_factory = dict_factory
        # Unions are instances now, not classes. We use different registry.
        self._union_registry = {}

    @property
    def dumping_strat(self) -> AttrsDumpingStrategy:
        """The default way of dumping ``attrs`` classes."""
        return (AttrsDumpingStrategy.AS_DICT
                if self.dumps_attrs is self.dumps_attrs_asdict
                else AttrsDumpingStrategy.AS_TUPLE)

    @dumping_strat.setter
    def dumping_strat(self, val: AttrsDumpingStrategy):
        if val is AttrsDumpingStrategy.AS_DICT:
            self.dumps_attrs = self.dumps_attrs_asdict
        else:
            self.dumps_attrs = self.dumps_attrs_astuple

    def register_dumps_hook(self, cls: Type[T], func: Callable[[T], Any]):
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        self.dumps.register(cls, func)

    def register_loads_hook(self, cl: Type[T],
                            func: Callable[[Any, Type], T]) -> None:
        """Register a primitive-to-class converter function for a type.

        The converter function should take two arguments:
          * a Python object to be converted,
          * the type to convert to

        and return the instance of the class. The type may seem redundant, but
        is sometimes needed (for example, when dealing with generic classes).
        """
        if isinstance(cl, _Union):
            self._union_registry[cl] = func
        else:
            self._loads.register(cl, lambda t, o: func(o, t))

    def loads(self, obj: Any, cl: Type):
        """Convert unstructured Python data structures to structured data."""
        # Unions aren't classes, but rather instances of typing._Union now.
        return (self._loads.dispatch(cl)(cl, obj) if not isinstance(cl, _Union)
                else self._loads_union(cl, obj))  # For Unions.

    # Classes to Python primitives.

    def _dumps(self, obj):
        """Convert given attrs classes to their primitive equivalents."""
        return (self.dumps_attrs(obj)
                if getattr(obj.__class__, "__attrs_attrs__", None) is not None
                else obj)

    def dumps_attrs_asdict(self, obj):
        """Our version of `attrs.asdict`, so we can call back to us."""
        attrs = obj.__class__.__attrs_attrs__
        rv = self._dict_factory()
        for a in attrs:
            name = a.name
            v = getattr(obj, name)
            rv[name] = self.dumps(v)
        return rv

    def dumps_attrs_astuple(self, obj):
        """Our version of `attrs.astuple`, so we can call back to us."""
        attrs = obj.__class__.__attrs_attrs__
        return tuple(self.dumps(getattr(obj, a.name)) for a in attrs)

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
            return self.loads_attrs(obj, cl)
        # We don't know what this is, so we complain loudly.
        msg = "Unsupported type: {0}. Register a loads hook for it.".format(cl)
        raise ValueError(msg)

    def _loads_call(self, cl, obj):
        """Just call ``cl`` with the given ``obj``.

        This is just an optimization on the ``_loads_default`` case, when we
        know we can skip the ``if`` s. Use for ``str``, ``bytes``, ``enum``,
        etc.
        """
        return cl(obj)

    # Attrs classes.

    def loads_attrs_fromtuple(self, obj: Sequence[Any], cl):
        """Load an attrs class from a sequence (tuple)."""
        conv_obj = []  # A list of converter parameters.
        for a, value in zip(cl.__attrs_attrs__, obj):
            # We detect the type by the validator.
            validator = a.validator
            converted = self._handle_attr_attribute(a.name, validator, value)
            conv_obj.append(converted)

        return cl(*conv_obj)

    def _handle_attr_attribute(self, name, validator, value):
        """Handle an individual attrs validator."""
        if validator is None:
            # No validator.
            return value
        elif isinstance(validator, _OptionalValidator):
            # This is an Optional[something]
            if value is None:
                return None
            return self._handle_attr_attribute(name, validator.validator,
                                               value)
        elif isinstance(validator, _InstanceOfValidator):
            type_ = validator.type
            return self._loads.dispatch(type_)(type_, value)
        else:
            # An unknown validator.
            return value

    def loads_attrs_fromdict(self, obj: Mapping, cl):
        """Load an attrs class from a mapping (dict)."""
        # For public use.
        conv_obj = obj.copy()  # Dict of converted parameters.
        for a in cl.__attrs_attrs__:
            name = a.name
            # We detect the type by the validator.
            validator = a.validator
            converted = self._handle_attr_mapping_attribute(name, validator,
                                                            obj)
            if converted is NOTHING:
                continue
            conv_obj[name] = converted

        return cl(**conv_obj)

    def _handle_attr_mapping_attribute(self, name, val, mapping):
        """Handle an individual attrs validator."""
        if val is None:
            # No validator.
            return mapping[name]
        elif isinstance(val, _OptionalValidator):
            # This is an Optional[something]
            if name not in mapping or mapping[name] is None:
                return NOTHING
            return self._handle_attr_mapping_attribute(name, val.validator,
                                                       mapping)
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
            conv = (self._loads.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._loads_union)
            return [conv(elem_type, e) for e in obj]

    def _loads_set(self, cl: Type[GenericMeta], obj: Iterable[T])\
            -> MutableSet[T]:
        """Convert an iterable into a potentially generic set."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return set(obj)
        else:
            elem_type = cl.__args__[0]
            conv = (self._loads.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._loads_union)
            return {conv(elem_type, e) for e in obj}

    def _loads_frozenset(self, cl: Type[GenericMeta], obj: Iterable[T])\
            -> FrozenSet[T]:
        """Convert an iterable into a potentially generic frozenset."""
        if not cl.__args__ or cl.__args__[0] is Any:
            return frozenset(obj)
        else:
            elem_type = cl.__args__[0]
            conv = (self._loads.dispatch(elem_type)
                    if not isinstance(elem_type, _Union)
                    else self._loads_union)
            return frozenset([conv(elem_type, e) for e in obj])

    def _loads_dict(self, cl: Type[GenericMeta], obj: Mapping[T, V])\
            -> Dict[T, V]:
        """Convert a mapping into a potentially generic dict."""
        if not cl.__args__ or cl.__args__ == (Any, Any):
            return dict(obj)
        else:
            key_type, val_type = cl.__args__
            if key_type is Any:
                val_conv = (self._loads.dispatch(val_type)
                            if not isinstance(val_type, _Union)
                            else self._loads_union)
                return {k: val_conv(val_type, v) for k, v in obj.items()}
            elif val_type is Any:
                key_conv = (self._loads.dispatch(key_type)
                            if not isinstance(key_type, _Union)
                            else self._loads_union)
                return {key_conv(key_type, k): v for k, v in obj.items()}
            else:
                key_conv = (self._loads.dispatch(key_type)
                            if not isinstance(key_type, _Union)
                            else self._loads_union)
                val_conv = (self._loads.dispatch(val_type)
                            if not isinstance(val_type, _Union)
                            else self._loads_union)
                return {key_conv(key_type, k): val_conv(val_type, v)
                        for k, v in obj.items()}

    def _loads_union(self, union: _Union, obj: Any):
        """Deal with converting a union.

        Note that optionals are unions that contain NoneType. We check for
        NoneType early and handle the case of obj being None, so
        disambiguation functions don't need to handle NoneType.
        """
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
                return self._loads.dispatch(other)(other, obj)

        # Getting here means either this is not an optional, or it's an
        # optional with more than one parameter.
        # Let's support only unions of attr classes for now.
        cl = self._get_dis_func(union)(obj)
        return self._loads.dispatch(cl)(cl, obj)

    def _loads_tuple(self, tup: Type[Tuple], obj: Iterable):
        """Deal with converting to a tuple."""
        tup_params = tup.__args__
        has_ellipsis = (tup_params and tup_params[-1] is Ellipsis)
        if tup_params is None or (has_ellipsis and tup_params[0] is Any):
            # Just a Tuple. (No generic information.)
            return tuple(obj)
        if has_ellipsis:
            # We're dealing with a homogenous tuple, Tuple[int, ...]
            tup_type = tup_params[0]
            conv = (self._loads.dispatch(tup_type)
                    if not isinstance(tup_type, _Union)
                    else self._loads_union)
            return tuple(conv(tup_type, e) for e in obj)
        else:
            # We're dealing with a heterogenous tuple.
            return tuple(self._loads.dispatch(t)(t, e)
                         if not isinstance(t, _Union)
                         else self._loads_union(t, e)
                         for t, e in zip(tup_params, obj))

    def _get_dis_func(self, union: Type) -> Callable[..., Type]:
        """Fetch or try creating a disambiguation function for a union."""
        if not all(hasattr(e, '__attrs_attrs__')
                   for e in union.__args__):
            raise ValueError('Only unions of attr classes supported '
                             'currently. Register a loads hook manually.')
        return create_uniq_field_dis_func(*union.__args__)
