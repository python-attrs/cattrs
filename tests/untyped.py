"""Strategies for attributes without types and accompanying classes."""

import keyword
import string
from enum import Enum
from typing import (
    Any,
    Deque,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
    Tuple,
)

import attr
from attr._make import _CountingAttr
from attrs import NOTHING, AttrsInstance, Factory, make_class
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy, booleans
from typing_extensions import TypeAlias

from . import FeatureFlag

PosArg = Any
PosArgs = tuple[PosArg]
KwArgs = dict[str, Any]
AttrsAndArgs: TypeAlias = tuple[type[AttrsInstance], PosArgs, KwArgs]

primitive_strategies = st.sampled_from(
    [
        (st.integers(), int),
        (st.floats(allow_nan=False), float),
        (st.text(), str),
        (st.binary(), bytes),
    ]
)


@st.composite
def enums_of_primitives(draw: st.DrawFn) -> Enum:
    """Generate enum classes with primitive values."""
    names = draw(
        st.sets(st.text(min_size=1).filter(lambda s: not s.endswith("_")), min_size=1)
    )
    n = len(names)
    vals = draw(
        st.one_of(
            st.sets(
                st.one_of(
                    st.integers(), st.floats(allow_nan=False), st.text(min_size=1)
                ),
                min_size=n,
                max_size=n,
            )
        )
    )
    return Enum("HypEnum", list(zip(names, vals)))


list_types = st.sampled_from([List, Sequence, MutableSequence])
deque_types = st.sampled_from([Deque, Sequence, MutableSequence])
set_types = st.sampled_from([Set, MutableSet])


@st.composite
def lists_of_primitives(draw):
    """Generate a strategy that yields tuples of list of primitives and types.

    For example, a sample value might be ([1,2], List[int]).
    """
    prim_strat, t = draw(primitive_strategies)
    list_t = draw(list_types.map(lambda list_t: list_t[t]) | list_types)
    return draw(st.lists(prim_strat)), list_t


@st.composite
def deques_of_primitives(draw):
    """Generate a strategy that yields tuples of list of primitives and types.

    For example, a sample value might be ([1,2], Deque[int]).
    """
    prim_strat, t = draw(primitive_strategies)
    deque_t = draw(deque_types.map(lambda deque_t: deque_t[t]) | deque_types)
    return draw(st.lists(prim_strat)), deque_t


@st.composite
def mut_sets_of_primitives(draw):
    """A strategy that generates mutable sets of primitives."""
    prim_strat, t = draw(primitive_strategies)
    set_t = draw(set_types.map(lambda set_t: set_t[t]) | set_types)
    return draw(st.sets(prim_strat)), set_t


@st.composite
def frozen_sets_of_primitives(draw):
    """A strategy that generates frozen sets of primitives."""
    prim_strat, t = draw(primitive_strategies)
    set_t = draw(st.just(Set) | st.just(Set[t]))
    return frozenset(draw(st.sets(prim_strat))), set_t


h_tuple_types = st.sampled_from([Tuple, Sequence])
h_tuples_of_primitives = primitive_strategies.flatmap(
    lambda e: st.tuples(
        st.lists(e[0]),
        st.one_of(st.sampled_from([Tuple[e[1], ...], Sequence[e[1]]]), h_tuple_types),
    )
).map(lambda e: (tuple(e[0]), e[1]))

dict_types = st.sampled_from([Dict, MutableMapping, Mapping])

seqs_of_primitives = st.one_of(lists_of_primitives(), h_tuples_of_primitives)
deque_seqs_of_primitives = st.one_of(deques_of_primitives(), h_tuples_of_primitives)
sets_of_primitives = st.one_of(mut_sets_of_primitives(), frozen_sets_of_primitives())


def create_generic_dict_type(type1, type2):
    """Create a strategy for generating parameterized dict types."""
    return st.one_of(
        dict_types,
        dict_types.map(lambda t: t[type1, type2]),
        dict_types.map(lambda t: t[Any, type2]),
        dict_types.map(lambda t: t[type1, Any]),
    )


def create_dict_and_type(tuple_of_strats):
    """Map two primitive strategies into a strategy for dict and type."""
    (prim_strat_1, type_1), (prim_strat_2, type_2) = tuple_of_strats

    return st.tuples(
        st.dictionaries(prim_strat_1, prim_strat_2),
        create_generic_dict_type(type_1, type_2),
    )


dicts_of_primitives = st.tuples(primitive_strategies, primitive_strategies).flatmap(
    create_dict_and_type
)


def gen_attr_names() -> Iterable[str]:
    """
    Generate names for attributes, 'a'...'z', then 'aa'...'zz'.
    ~702 different attribute names should be enough in practice.
    Some short strings (such as 'as') are keywords, so we skip them.

    Every second attribute name is private (starts with an underscore).
    """
    lc = string.ascii_lowercase
    has_underscore = False
    for c in lc:
        yield c if not has_underscore else "_" + c
        has_underscore = not has_underscore
    for outer in lc:
        for inner in lc:
            res = outer + inner
            if keyword.iskeyword(res):
                continue
            yield outer + inner


def _create_hyp_class(
    attrs_and_strategy: list[tuple[_CountingAttr, st.SearchStrategy[PosArgs]]],
    frozen=None,
) -> SearchStrategy[AttrsAndArgs]:
    """
    A helper function for Hypothesis to generate attrs classes.

    The result is a tuple: an attrs class, a tuple of values to
    instantiate it, and a kwargs dict for kw-only attributes.
    """

    def key(t):
        return (t[0].default is not NOTHING, t[0].kw_only)

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat if not a[0].kw_only)
    kwargs = {}
    for attr_name, attr_and_strat in zip(gen_attr_names(), attrs_and_strat):
        if attr_and_strat[0].kw_only:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            kwargs[attr_name] = attr_and_strat[1]
    return st.tuples(
        st.builds(
            lambda f: make_class(
                "HypClass", dict(zip(gen_attr_names(), attrs)), frozen=f
            ),
            st.booleans() if frozen is None else st.just(frozen),
        ),
        st.tuples(*vals),
        st.fixed_dictionaries(kwargs),
    )


def just_class(tup):
    nested_cl = tup[1][0]
    default = attr.Factory(nested_cl)
    combined_attrs = list(tup[0])
    combined_attrs.append((attr.ib(default=default), st.just(nested_cl())))
    return _create_hyp_class(combined_attrs)


def just_class_with_type(tup: tuple) -> SearchStrategy[AttrsAndArgs]:
    nested_cl = tup[1][0]

    def make_with_default(takes_self: bool) -> SearchStrategy[AttrsAndArgs]:
        combined_attrs = list(tup[0])
        combined_attrs.append(
            (
                attr.ib(
                    default=(
                        Factory(
                            nested_cl if not takes_self else lambda _: nested_cl(),
                            takes_self=takes_self,
                        )
                    ),
                    type=nested_cl,
                ),
                st.just(nested_cl()),
            )
        )
        return _create_hyp_class(combined_attrs)

    return booleans().flatmap(make_with_default)


def just_frozen_class_with_type(tup):
    nested_cl = tup[1][0]
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (attr.ib(default=nested_cl(), type=nested_cl), st.just(nested_cl()))
    )
    return _create_hyp_class(combined_attrs)


def list_of_class(tup: tuple) -> SearchStrategy[AttrsAndArgs]:
    nested_cl = tup[1][0]

    def make_with_default(takes_self: bool) -> SearchStrategy[AttrsAndArgs]:
        combined_attrs = list(tup[0])
        combined_attrs.append(
            (
                attr.ib(
                    default=(
                        Factory(lambda: [nested_cl()])
                        if not takes_self
                        else Factory(lambda _: [nested_cl()], takes_self=True)
                    ),
                    type=list[nested_cl],
                ),
                st.just([nested_cl()]),
            )
        )
        return _create_hyp_class(combined_attrs)

    return booleans().flatmap(make_with_default)


def list_of_class_with_type(tup: tuple) -> SearchStrategy[AttrsAndArgs]:
    nested_cl = tup[1][0]

    def make_with_default(takes_self: bool) -> SearchStrategy[AttrsAndArgs]:
        default = (
            Factory(lambda: [nested_cl()])
            if not takes_self
            else Factory(lambda _: [nested_cl()], takes_self=True)
        )
        combined_attrs = list(tup[0])
        combined_attrs.append(
            (attr.ib(default=default, type=List[nested_cl]), st.just([nested_cl()]))
        )
        return _create_hyp_class(combined_attrs)

    return booleans().flatmap(make_with_default)


def dict_of_class(tup):
    nested_cl = tup[1][0]
    default = attr.Factory(lambda: {"cls": nested_cl()})
    combined_attrs = list(tup[0])
    combined_attrs.append((attr.ib(default=default), st.just({"cls": nested_cl()})))
    return _create_hyp_class(combined_attrs)


def _create_hyp_nested_strategy(
    simple_class_strategy: SearchStrategy,
) -> SearchStrategy:
    """
    Create a recursive attrs class.
    Given a strategy for building (simpler) classes, create and return
    a strategy for building classes that have as an attribute:
        * just the simpler class
        * a list of simpler classes
        * a dict mapping the string "cls" to a simpler class.
    """

    # A strategy producing tuples of the form ([list of attributes], <given
    # class strategy>).
    attrs_and_classes = st.tuples(lists_of_attrs(defaults=True), simple_class_strategy)

    return (
        attrs_and_classes.flatmap(just_class)
        | attrs_and_classes.flatmap(just_class_with_type)
        | attrs_and_classes.flatmap(list_of_class)
        | attrs_and_classes.flatmap(list_of_class_with_type)
        | attrs_and_classes.flatmap(dict_of_class)
        | attrs_and_classes.flatmap(just_frozen_class_with_type)
    )


@st.composite
def bare_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields values
    appropriate for that attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(st.booleans())):
        default = None
    return (
        attr.ib(
            default=default, kw_only=draw(st.booleans()) if kw_only is None else kw_only
        ),
        st.just(None),
    )


@st.composite
def int_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields ints for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(st.booleans())):
        default = draw(st.integers())
    return (
        attr.ib(
            default=default, kw_only=draw(st.booleans()) if kw_only is None else kw_only
        ),
        st.integers(),
    )


@st.composite
def str_attrs(draw, defaults=None, type_annotations=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields strs for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(st.booleans())):
        default = draw(st.text())
    if (type_annotations is None and draw(st.booleans())) or type_annotations:
        type = str
    else:
        type = None
    return (
        attr.ib(
            default=default,
            type=type,
            kw_only=draw(st.booleans()) if kw_only is None else kw_only,
        ),
        st.text(),
    )


@st.composite
def float_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields floats for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(st.booleans())):
        default = draw(st.floats(allow_nan=False))
    return (
        attr.ib(
            default=default, kw_only=draw(st.booleans()) if kw_only is None else kw_only
        ),
        st.floats(allow_nan=False),
    )


@st.composite
def dict_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.
    """
    default = NOTHING
    val_strat = st.dictionaries(keys=st.text(), values=st.integers())
    if defaults is True or (defaults is None and draw(st.booleans())):
        default_val = draw(val_strat)
        default = attr.Factory(lambda: default_val)
    return (
        attr.ib(
            default=default, kw_only=draw(st.booleans()) if kw_only is None else kw_only
        ),
        val_strat,
    )


@st.composite
def optional_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields values
    for that attribute. The strategy generates optional integers.
    """
    default = NOTHING
    val_strat = st.integers() | st.none()
    if defaults is True or (defaults is None and draw(st.booleans())):
        default = draw(val_strat)

    return (
        attr.ib(
            default=default, kw_only=draw(st.booleans()) if kw_only is None else kw_only
        ),
        val_strat,
    )


def simple_attrs(defaults=None, kw_only=None):
    return (
        bare_attrs(defaults, kw_only=kw_only)
        | int_attrs(defaults, kw_only=kw_only)
        | str_attrs(defaults, kw_only=kw_only)
        | float_attrs(defaults, kw_only=kw_only)
        | dict_attrs(defaults, kw_only=kw_only)
        | optional_attrs(defaults, kw_only=kw_only)
    )


def lists_of_attrs(defaults=None, min_size=0, kw_only=None):
    # Python functions support up to 255 arguments.
    return st.lists(
        simple_attrs(defaults, kw_only), min_size=min_size, max_size=10
    ).map(lambda lst: sorted(lst, key=lambda t: t[0]._default is not NOTHING))


def simple_classes(defaults=None, min_attrs=0, frozen=None, kw_only=None):
    """
    Return a strategy that yields tuples of simple classes and values to
    instantiate them.
    """
    return lists_of_attrs(defaults, min_size=min_attrs, kw_only=kw_only).flatmap(
        lambda attrs_and_strategy: _create_hyp_class(attrs_and_strategy, frozen=frozen)
    )


def nested_classes(
    takes_self: FeatureFlag = "sometimes",
) -> SearchStrategy[AttrsAndArgs]:
    # Ok, so st.recursive works by taking a base strategy (in this case,
    # simple_classes) and a special function. This function receives a strategy,
    # and returns another strategy (building on top of the base strategy).
    return st.recursive(simple_classes(defaults=True), _create_hyp_nested_strategy)
