"""Tests for metadata functionality."""
import sys
from collections import OrderedDict
from typing import Any, Dict, FrozenSet, List, Tuple

import attr
from attr import NOTHING
from hypothesis.strategies import (
    booleans,
    composite,
    dictionaries,
    floats,
    frozensets,
    integers,
    just,
    lists,
    recursive,
    sets,
    text,
    tuples,
)

from .. import gen_attr_names, make_class

is_39_or_later = sys.version_info[:2] >= (3, 9)


def simple_typed_classes(defaults=None, min_attrs=0):
    """Similar to simple_classes, but the attributes have metadata."""
    return lists_of_typed_attrs(defaults, min_size=min_attrs).flatmap(
        _create_hyp_class
    )


def lists_of_typed_attrs(defaults=None, min_size=0):
    # Python functions support up to 255 arguments.
    return lists(
        simple_typed_attrs(defaults), min_size=min_size, max_size=50
    ).map(lambda l: sorted(l, key=lambda t: t[0]._default is not NOTHING))


def simple_typed_attrs(defaults=None):
    if not is_39_or_later:
        return (
            bare_typed_attrs(defaults)
            | int_typed_attrs(defaults)
            | str_typed_attrs(defaults)
            | float_typed_attrs(defaults)
            | dict_typed_attrs(defaults)
        )
    else:
        return (
            bare_typed_attrs(defaults)
            | int_typed_attrs(defaults)
            | str_typed_attrs(defaults)
            | float_typed_attrs(defaults)
            | dict_typed_attrs(defaults)
            | new_dict_typed_attrs(defaults)
            | set_typed_attrs(defaults)
            | list_typed_attrs(defaults)
            | frozenset_typed_attrs(defaults)
            | homo_tuple_typed_attrs(defaults)
        )


def _create_hyp_class(attrs_and_strategy):
    """
    A helper function for Hypothesis to generate attrs classes.

    The result is a tuple: an attrs class, and a tuple of values to
    instantiate it.
    """

    def key(t):
        return t[0].default is not attr.NOTHING

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat)
    return tuples(
        just(
            make_class("HypClass", OrderedDict(zip(gen_attr_names(), attrs)))
        ),
        tuples(*vals),
    )


@composite
def bare_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields values
    appropriate for that attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = None
    return (attr.ib(type=Any, default=default), just(None))


@composite
def int_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields ints for that
    attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(integers())
    return (attr.ib(type=int, default=default), integers())


@composite
def str_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields strs for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(text())
    return (attr.ib(type=str, default=default), text())


@composite
def float_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields floats for that
    attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(floats())
    return (attr.ib(type=float, default=default), floats())


@composite
def dict_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.
    """
    default = attr.NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (attr.ib(type=Dict[str, int], default=default), val_strat)


@composite
def new_dict_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.

    Uses the new 3.9 dict annotation.
    """
    default = attr.NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (attr.ib(type=dict[str, int], default=default), val_strat)


@composite
def set_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields sets
    for that attribute. The sets contain integers.
    """
    default = attr.NOTHING
    val_strat = sets(integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (attr.ib(type=set[int], default=default), val_strat)


@composite
def frozenset_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields frozensets
    for that attribute. The frozensets contain integers.
    """
    default = attr.NOTHING
    val_strat = frozensets(integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (
        attr.ib(
            type=frozenset[int] if draw(booleans()) else FrozenSet[int],
            default=default,
        ),
        val_strat,
    )


@composite
def list_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain floats.
    """
    default = attr.NOTHING
    val_strat = lists(floats(allow_infinity=False, allow_nan=False))
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (
        attr.ib(
            type=list[float] if draw(booleans()) else List[float],
            default=default,
        ),
        val_strat,
    )


@composite
def homo_tuple_typed_attrs(draw, defaults=None):
    """
    Generate a tuple of an attribute and a strategy that yields homogenous
    tuples for that attribute. The tuples contain strings.
    """
    default = attr.NOTHING
    val_strat = tuples(text(), text(), text())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (
        attr.ib(
            type=tuple[str, ...] if draw(booleans()) else Tuple[str, ...],
            default=default,
        ),
        val_strat,
    )


def just_class(tup):
    # tup: Tuple[List[Tuple[_CountingAttr, Strategy]],
    #            Tuple[Type, Sequence[Any]]]
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: nested_cl(*nested_cl_args))
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=nested_cl, default=default),
            just(nested_cl(*nested_cl_args)),
        )
    )
    return _create_hyp_class(combined_attrs)


def list_of_class(tup):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: [nested_cl(*nested_cl_args)])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=List[nested_cl], default=default),
            just([nested_cl(*nested_cl_args)]),
        )
    )
    return _create_hyp_class(combined_attrs)


def new_list_of_class(tup):
    """Uses the new 3.9 list type annotation."""
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: [nested_cl(*nested_cl_args)])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=list[nested_cl], default=default),
            just([nested_cl(*nested_cl_args)]),
        )
    )
    return _create_hyp_class(combined_attrs)


def dict_of_class(tup):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: {"cls": nested_cl(*nested_cl_args)})
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=Dict[str, nested_cl], default=default),
            just({"cls": nested_cl(*nested_cl_args)}),
        )
    )
    return _create_hyp_class(combined_attrs)


def _create_hyp_nested_strategy(simple_class_strategy):
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
    attrs_and_classes = tuples(lists_of_typed_attrs(), simple_class_strategy)

    return (
        attrs_and_classes.flatmap(just_class)
        | attrs_and_classes.flatmap(list_of_class)
        | attrs_and_classes.flatmap(dict_of_class)
    )


nested_typed_classes = recursive(
    simple_typed_classes(), _create_hyp_nested_strategy
)
