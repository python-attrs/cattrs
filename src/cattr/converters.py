from enum import Enum
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from attr import resolve_types, has as attrs_has

from ._compat import (
    get_origin,
    is_bare,
    is_frozenset,
    is_generic,
    is_mapping,
    is_mutable_set,
    is_sequence,
    is_tuple,
    is_union_type,
    is_annotated,
    has,
    fields,
    has_with_generic,
    Set,
    MutableSet,
    Sequence,
    MutableSequence,
    Mapping,
    MutableMapping,
)
from .disambiguators import create_uniq_field_dis_func
from .dispatch import MultiStrategyDispatch
from .gen import (
    AttributeOverride,
    make_dict_structure_fn,
    make_dict_unstructure_fn,
    make_iterable_unstructure_fn,
    make_mapping_unstructure_fn,
)
from collections import Counter

NoneType = type(None)
T = TypeVar("T")
V = TypeVar("V")


class UnstructureStrategy(Enum):
    """`attrs` classes unstructuring strategies."""

    AS_DICT = "asdict"
    AS_TUPLE = "astuple"


def _subclass(typ):
    """ a shortcut """
    return lambda cls: issubclass(cls, typ)


class Converter(object):
    """Converts between structured and unstructured data."""

    __slots__ = (
        "_dis_func_cache",
        "_unstructure_func",
        "_unstructure_attrs",
        "_structure_attrs",
        "_dict_factory",
        "_union_struct_registry",
        "_structure_func",
    )

    def __init__(
        self,
        dict_factory: Callable[[], Any] = dict,
        unstruct_strat: UnstructureStrategy = UnstructureStrategy.AS_DICT,
    ) -> None:
        unstruct_strat = UnstructureStrategy(unstruct_strat)

        # Create a per-instance cache.
        if unstruct_strat is UnstructureStrategy.AS_DICT:
            self._unstructure_attrs = self.unstructure_attrs_asdict
            self._structure_attrs = self.structure_attrs_fromdict
        else:
            self._unstructure_attrs = self.unstructure_attrs_astuple
            self._structure_attrs = self.structure_attrs_fromtuple

        self._dis_func_cache = lru_cache()(self._get_dis_func)

        self._unstructure_func = MultiStrategyDispatch(
            self._unstructure_identity
        )
        self._unstructure_func.register_cls_list(
            [
                (bytes, self._unstructure_identity),
                (str, self._unstructure_identity),
            ]
        )
        self._unstructure_func.register_func_list(
            [
                (is_mapping, self._unstructure_mapping),
                (is_sequence, self._unstructure_seq),
                (is_mutable_set, self._unstructure_seq),
                (is_frozenset, self._unstructure_seq),
                (_subclass(Enum), self._unstructure_enum),
                (has, self._unstructure_attrs),
                (is_union_type, self._unstructure_union),
            ]
        )

        # Per-instance register of to-attrs converters.
        # Singledispatch dispatches based on the first argument, so we
        # store the function and switch the arguments in self.loads.
        self._structure_func = MultiStrategyDispatch(self._structure_default)
        self._structure_func.register_func_list(
            [
                (is_sequence, self._structure_list),
                (is_mutable_set, self._structure_set),
                (is_frozenset, self._structure_frozenset),
                (is_tuple, self._structure_tuple),
                (is_mapping, self._structure_dict),
                (is_union_type, self._structure_union),
                (has, self._structure_attrs),
            ]
        )
        # Strings are sequences.
        self._structure_func.register_cls_list(
            [
                (
                    str,
                    self._structure_call,
                ),
                (bytes, self._structure_call),
                (int, self._structure_call),
                (float, self._structure_call),
                (Enum, self._structure_call),
            ]
        )

        self._dict_factory = dict_factory

        # Unions are instances now, not classes. We use different registries.
        self._union_struct_registry: Dict[
            Any, Callable[[Any, Type[T]], T]
        ] = {}

    def unstructure(self, obj: Any, unstructure_as=None) -> Any:
        return self._unstructure_func.dispatch(
            obj.__class__ if unstructure_as is None else unstructure_as
        )(obj)

    @property
    def unstruct_strat(self) -> UnstructureStrategy:
        """The default way of unstructuring ``attrs`` classes."""
        return (
            UnstructureStrategy.AS_DICT
            if self._unstructure_attrs == self.unstructure_attrs_asdict
            else UnstructureStrategy.AS_TUPLE
        )

    def register_unstructure_hook(
        self, cls: Any, func: Callable[[T], Any]
    ) -> None:
        """Register a class-to-primitive converter function for a class.

        The converter function should take an instance of the class and return
        its Python equivalent.
        """
        if attrs_has(cls):
            resolve_types(cls)
        if is_union_type(cls):
            self._unstructure_func.register_func_list(
                [(lambda t: t == cls, func)]
            )
        else:
            self._unstructure_func.register_cls_list([(cls, func)])

    def register_unstructure_hook_func(
        self, check_func: Callable[[Any], bool], func: Callable[[T], Any]
    ):
        """Register a class-to-primitive converter function for a class, using
        a function to check if it's a match.
        """
        self._unstructure_func.register_func_list([(check_func, func)])

    def register_structure_hook(
        self, cl: Any, func: Callable[[Any, Type[T]], T]
    ):
        """Register a primitive-to-class converter function for a type.

        The converter function should take two arguments:
          * a Python object to be converted,
          * the type to convert to

        and return the instance of the class. The type may seem redundant, but
        is sometimes needed (for example, when dealing with generic classes).
        """
        if attrs_has(cl):
            resolve_types(cl)
        if is_union_type(cl):
            self._union_struct_registry[cl] = func
        else:
            self._structure_func.register_cls_list([(cl, func)])

    def register_structure_hook_func(
        self,
        check_func: Callable[[Type[T]], bool],
        func: Callable[[Any, Type[T]], T],
    ):
        """Register a class-to-primitive converter function for a class, using
        a function to check if it's a match.
        """
        self._structure_func.register_func_list([(check_func, func)])

    def structure(self, obj: Any, cl: Type[T]) -> T:
        """Convert unstructured Python data structures to structured data."""

        return self._structure_func.dispatch(cl)(obj, cl)

    # Classes to Python primitives.
    def unstructure_attrs_asdict(self, obj) -> Dict[str, Any]:
        """Our version of `attrs.asdict`, so we can call back to us."""
        attrs = fields(obj.__class__)
        dispatch = self._unstructure_func.dispatch
        rv = self._dict_factory()
        for a in attrs:
            name = a.name
            v = getattr(obj, name)
            rv[name] = dispatch(a.type or v.__class__)(v)
        return rv

    def unstructure_attrs_astuple(self, obj) -> Tuple[Any, ...]:
        """Our version of `attrs.astuple`, so we can call back to us."""
        attrs = fields(obj.__class__)
        dispatch = self._unstructure_func.dispatch
        res = list()
        for a in attrs:
            name = a.name
            v = getattr(obj, name)
            res.append(dispatch(a.type or v.__class__)(v))
        return tuple(res)

    def _unstructure_enum(self, obj):
        """Convert an enum to its value."""
        return obj.value

    def _unstructure_identity(self, obj):
        """Just pass it through."""
        return obj

    def _unstructure_seq(self, seq):
        """Convert a sequence to primitive equivalents."""
        # We can reuse the sequence class, so tuples stay tuples.
        dispatch = self._unstructure_func.dispatch
        return seq.__class__(dispatch(e.__class__)(e) for e in seq)

    def _unstructure_mapping(self, mapping):
        """Convert a mapping of attr classes to primitive equivalents."""

        # We can reuse the mapping class, so dicts stay dicts and OrderedDicts
        # stay OrderedDicts.
        dispatch = self._unstructure_func.dispatch
        return mapping.__class__(
            (dispatch(k.__class__)(k), dispatch(v.__class__)(v))
            for k, v in mapping.items()
        )

    def _unstructure_union(self, obj):
        """
        Unstructure an object as a union.

        By default, just unstructures the instance.
        """
        return self._unstructure_func.dispatch(obj.__class__)(obj)

    # Python primitives to classes.

    def _structure_default(self, obj, cl):
        """This is the fallthrough case. Everything is a subclass of `Any`.

        A special condition here handles ``attrs`` classes.

        Bare optionals end here too (optionals with arguments are unions.) We
        treat bare optionals as Any.
        """
        if cl is Any or cl is Optional or cl is None:
            return obj

        if is_generic(cl):
            fn = make_dict_structure_fn(cl, self)
            self.register_structure_hook(cl, fn)
            return fn(obj)

        # We don't know what this is, so we complain loudly.
        msg = (
            "Unsupported type: {0}. Register a structure hook for "
            "it.".format(cl)
        )
        raise ValueError(msg)

    @staticmethod
    def _structure_call(obj, cl):
        """Just call ``cl`` with the given ``obj``.

        This is just an optimization on the ``_structure_default`` case, when
        we know we can skip the ``if`` s. Use for ``str``, ``bytes``, ``enum``,
        etc.
        """
        return cl(obj)

    # Attrs classes.

    def structure_attrs_fromtuple(
        self, obj: Tuple[Any, ...], cl: Type[T]
    ) -> T:
        """Load an attrs class from a sequence (tuple)."""
        conv_obj = []  # A list of converter parameters.
        for a, value in zip(fields(cl), obj):  # type: ignore
            # We detect the type by the metadata.
            converted = self._structure_attr_from_tuple(a, a.name, value)
            conv_obj.append(converted)

        return cl(*conv_obj)  # type: ignore

    def _structure_attr_from_tuple(self, a, _, value):
        """Handle an individual attrs attribute."""
        type_ = a.type
        if type_ is None:
            # No type metadata.
            return value
        return self._structure_func.dispatch(type_)(value, type_)

    def structure_attrs_fromdict(
        self, obj: Mapping[str, Any], cl: Type[T]
    ) -> T:
        """Instantiate an attrs class from a mapping (dict)."""
        # For public use.

        conv_obj = {}  # Start with a fresh dict, to ignore extra keys.
        dispatch = self._structure_func.dispatch
        for a in fields(cl):  # type: ignore
            # We detect the type by metadata.
            type_ = a.type
            name = a.name

            try:
                val = obj[name]
            except KeyError:
                continue

            if name[0] == "_":
                name = name[1:]

            conv_obj[name] = (
                dispatch(type_)(val, type_) if type_ is not None else val
            )

        return cl(**conv_obj)  # type: ignore

    def _structure_list(self, obj, cl):
        """Convert an iterable to a potentially generic list."""
        if is_bare(cl) or cl.__args__[0] is Any:
            return [e for e in obj]
        else:
            elem_type = cl.__args__[0]
            return [
                self._structure_func.dispatch(elem_type)(e, elem_type)
                for e in obj
            ]

    def _structure_set(self, obj, cl):
        """Convert an iterable into a potentially generic set."""
        if is_bare(cl) or cl.__args__[0] is Any:
            return set(obj)
        else:
            elem_type = cl.__args__[0]
            return {
                self._structure_func.dispatch(elem_type)(e, elem_type)
                for e in obj
            }

    def _structure_frozenset(self, obj, cl):
        """Convert an iterable into a potentially generic frozenset."""
        if is_bare(cl) or cl.__args__[0] is Any:
            return frozenset(obj)
        else:
            elem_type = cl.__args__[0]
            dispatch = self._structure_func.dispatch
            return frozenset(dispatch(elem_type)(e, elem_type) for e in obj)

    def _structure_dict(self, obj, cl):
        """Convert a mapping into a potentially generic dict."""
        if is_bare(cl) or cl.__args__ == (Any, Any):
            return dict(obj)
        else:
            key_type, val_type = cl.__args__
            if key_type is Any:
                val_conv = self._structure_func.dispatch(val_type)
                return {k: val_conv(v, val_type) for k, v in obj.items()}
            elif val_type is Any:
                key_conv = self._structure_func.dispatch(key_type)
                return {key_conv(k, key_type): v for k, v in obj.items()}
            else:
                key_conv = self._structure_func.dispatch(key_type)
                val_conv = self._structure_func.dispatch(val_type)
                return {
                    key_conv(k, key_type): val_conv(v, val_type)
                    for k, v in obj.items()
                }

    def _structure_union(self, obj, union):
        """Deal with converting a union."""
        # Unions with NoneType in them are basically optionals.
        # We check for NoneType early and handle the case of obj being None,
        # so disambiguation functions don't need to handle NoneType.
        union_params = union.__args__
        if NoneType in union_params:  # type: ignore
            if obj is None:
                return None
            if len(union_params) == 2:
                # This is just a NoneType and something else.
                other = (
                    union_params[0]
                    if union_params[1] is NoneType  # type: ignore
                    else union_params[1]
                )
                # We can't actually have a Union of a Union, so this is safe.
                return self._structure_func.dispatch(other)(obj, other)

        # Check the union registry first.
        handler = self._union_struct_registry.get(union)
        if handler is not None:
            return handler(obj, union)

        # Getting here means either this is not an optional, or it's an
        # optional with more than one parameter.
        # Let's support only unions of attr classes for now.
        cl = self._dis_func_cache(union)(obj)
        return self._structure_func.dispatch(cl)(obj, cl)

    def _structure_tuple(self, obj, tup: Type[T]):
        """Deal with converting to a tuple."""
        if tup in (Tuple, tuple):
            tup_params = None
        else:
            tup_params = tup.__args__
        has_ellipsis = tup_params and tup_params[-1] is Ellipsis
        if tup_params is None or (has_ellipsis and tup_params[0] is Any):
            # Just a Tuple. (No generic information.)
            return tuple(obj)
        if has_ellipsis:
            # We're dealing with a homogenous tuple, Tuple[int, ...]
            tup_type = tup_params[0]
            conv = self._structure_func.dispatch(tup_type)
            return tuple(conv(e, tup_type) for e in obj)
        else:
            # We're dealing with a heterogenous tuple.
            return tuple(
                self._structure_func.dispatch(t)(e, t)
                for t, e in zip(tup_params, obj)
            )

    @staticmethod
    def _get_dis_func(union):
        # type: (Type) -> Callable[..., Type]
        """Fetch or try creating a disambiguation function for a union."""
        union_types = union.__args__
        if NoneType in union_types:  # type: ignore
            # We support unions of attrs classes and NoneType higher in the
            # logic.
            union_types = tuple(
                e for e in union_types if e is not NoneType  # type: ignore
            )

        if not all(has(get_origin(e) or e) for e in union_types):
            raise ValueError(
                "Only unions of attr classes supported "
                "currently. Register a loads hook manually."
            )
        return create_uniq_field_dis_func(*union_types)


class GenConverter(Converter):
    """A converter which generates specialized un/structuring functions."""

    __slots__ = (
        "omit_if_default",
        "forbid_extra_keys",
        "type_overrides",
        "_unstruct_collection_overrides",
    )

    def __init__(
        self,
        dict_factory: Callable[[], Any] = dict,
        unstruct_strat: UnstructureStrategy = UnstructureStrategy.AS_DICT,
        omit_if_default: bool = False,
        forbid_extra_keys: bool = False,
        type_overrides: Mapping[Type, AttributeOverride] = {},
        unstruct_collection_overrides: Mapping[Type, Callable] = {},
    ):
        super().__init__(
            dict_factory=dict_factory, unstruct_strat=unstruct_strat
        )
        self.omit_if_default = omit_if_default
        self.forbid_extra_keys = forbid_extra_keys
        self.type_overrides = dict(type_overrides)

        self._unstruct_collection_overrides = unstruct_collection_overrides

        # Do a little post-processing magic to make things easier for users.
        co = unstruct_collection_overrides

        # abc.Set overrides, if defined, apply to abc.MutableSets and sets
        if Set in co:
            if MutableSet not in co:
                co[MutableSet] = co[Set]

        # abc.MutableSet overrrides, if defined, apply to sets
        if MutableSet in co:
            if set not in co:
                co[set] = co[MutableSet]

        # abc.Sequence overrides, if defined, can apply to MutableSequences, lists and tuples
        if Sequence in co:
            if MutableSequence not in co:
                co[MutableSequence] = co[Sequence]
            if tuple not in co:
                co[tuple] = co[Sequence]

        # abc.MutableSequence overrides, if defined, can apply to lists
        if MutableSequence in co:
            if list not in co:
                co[list] = co[MutableSequence]

        # abc.Mapping overrides, if defined, can apply to MutableMappings
        if Mapping in co:
            if MutableMapping not in co:
                co[MutableMapping] = co[Mapping]

        # abc.MutableMapping overrides, if defined, can apply to dicts
        if MutableMapping in co:
            if dict not in co:
                co[dict] = co[MutableMapping]

        # builtins.dict overrides, if defined, can apply to counters
        if dict in co:
            if Counter not in co:
                co[Counter] = co[dict]

        if unstruct_strat is UnstructureStrategy.AS_DICT:
            # Override the attrs handler.
            self._unstructure_func.register_func_list(
                [
                    (
                        has_with_generic,
                        self.gen_unstructure_attrs_fromdict,
                        True,
                    ),
                ]
            )
            self._structure_func.register_func_list(
                [
                    (has, self.gen_structure_attrs_fromdict, True),
                ]
            )

        self._unstructure_func.register_func_list(
            [
                (is_annotated, self.gen_unstructure_annotated, True),
                (
                    is_sequence,
                    self.gen_unstructure_iterable,
                    True,
                ),
                (is_mapping, self.gen_unstructure_mapping, True),
                (
                    is_mutable_set,
                    lambda cl: self.gen_unstructure_iterable(
                        cl, unstructure_to=set
                    ),
                    True,
                ),
                (
                    is_frozenset,
                    lambda cl: self.gen_unstructure_iterable(
                        cl, unstructure_to=frozenset
                    ),
                    True,
                ),
            ]
        )
        self._structure_func.register_func_list(
            [(is_annotated, self.gen_structure_annotated, True)]
        )

    def gen_unstructure_annotated(self, type):
        origin = type.__origin__
        h = self._unstructure_func.dispatch(origin)
        return h

    def gen_structure_annotated(self, type):
        origin = type.__origin__
        h = self._structure_func.dispatch(origin)
        return h

    def gen_unstructure_attrs_fromdict(self, cl: Type[T]) -> Dict[str, Any]:
        origin = get_origin(cl)
        if origin is not None:
            cl = origin
        attribs = fields(cl)
        if any(isinstance(a.type, str) for a in attribs):
            # PEP 563 annotations - need to be resolved.
            resolve_types(cl)
        attrib_overrides = {
            a.name: self.type_overrides[a.type]
            for a in attribs
            if a.type in self.type_overrides
        }

        h = make_dict_unstructure_fn(
            cl, self, omit_if_default=self.omit_if_default, **attrib_overrides
        )
        self._unstructure_func.register_cls_list([(cl, h)], direct=True)
        return h

    def gen_structure_attrs_fromdict(self, cl: Type[T]) -> T:
        attribs = fields(cl)
        if any(isinstance(a.type, str) for a in attribs):
            # PEP 563 annotations - need to be resolved.
            resolve_types(cl)
        attrib_overrides = {
            a.name: self.type_overrides[a.type]
            for a in attribs
            if a.type in self.type_overrides
        }
        h = make_dict_structure_fn(
            cl,
            self,
            _cattrs_forbid_extra_keys=self.forbid_extra_keys,
            **attrib_overrides
        )
        self._structure_func.register_cls_list([(cl, h)], direct=True)
        # only direct dispatch so that subclasses get separately generated
        return h

    def gen_unstructure_iterable(self, cl: Any, unstructure_to=None):
        unstructure_to = self._unstruct_collection_overrides.get(
            get_origin(cl) or cl, unstructure_to or list
        )
        h = make_iterable_unstructure_fn(
            cl, self, unstructure_to=unstructure_to
        )
        self._unstructure_func.register_cls_list([(cl, h)], direct=True)
        return h

    def gen_unstructure_mapping(self, cl: Any, unstructure_to=None):
        unstructure_to = self._unstruct_collection_overrides.get(
            get_origin(cl) or cl, unstructure_to or dict
        )
        h = make_mapping_unstructure_fn(
            cl, self, unstructure_to=unstructure_to
        )
        self._unstructure_func.register_cls_list([(cl, h)], direct=True)
        return h
