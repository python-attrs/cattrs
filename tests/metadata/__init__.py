"""Tests for metadata functionality."""
import sys
from collections import OrderedDict
from collections.abc import MutableSequence as AbcMutableSequence
from collections.abc import MutableSet as AbcMutableSet
from collections.abc import Sequence as AbcSequence
from collections.abc import Set as AbcSet
from dataclasses import field, make_dataclass
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    List,
    MutableSequence,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

import attr
from attr import NOTHING, Factory
from attr._make import _CountingAttr
from hypothesis.strategies import (
    SearchStrategy,
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
PosArg = Any
PosArgs = Tuple[Any]
T = TypeVar("T")


def simple_typed_classes(defaults=None, min_attrs=0, frozen=False):
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults, min_size=min_attrs, for_frozen=frozen
    ).flatmap(partial(_create_hyp_class, frozen=frozen))


def simple_typed_dataclasses(defaults=None, min_attrs=0, frozen=False):
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        for_frozen=frozen,
        allow_mutable_defaults=False,
    ).flatmap(partial(_create_dataclass, frozen=frozen))


def simple_typed_classes_and_strats(
    defaults=None, min_attrs=0
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
    """Yield tuples of (class, (strategies))."""
    return lists_of_typed_attrs(defaults, min_size=min_attrs).flatmap(
        _create_hyp_class_and_strat
    )


def lists_of_typed_attrs(
    defaults=None, min_size=0, for_frozen=False, allow_mutable_defaults=True
) -> SearchStrategy[List[Tuple[_CountingAttr, SearchStrategy[PosArg]]]]:
    # Python functions support up to 255 arguments.
    return lists(
        simple_typed_attrs(
            defaults,
            for_frozen=for_frozen,
            allow_mutable_defaults=allow_mutable_defaults,
        ),
        min_size=min_size,
        max_size=50,
    ).map(lambda l: sorted(l, key=lambda t: t[0]._default is not NOTHING))


def simple_typed_attrs(
    defaults=None, for_frozen=False, allow_mutable_defaults=True
) -> SearchStrategy[Tuple[_CountingAttr, SearchStrategy[PosArgs]]]:
    if not is_39_or_later:
        res = (
            bare_typed_attrs(defaults)
            | int_typed_attrs(defaults)
            | str_typed_attrs(defaults)
            | float_typed_attrs(defaults)
        )
        if not for_frozen:
            res = (
                res
                | dict_typed_attrs(defaults, allow_mutable_defaults)
                | mutable_seq_typed_attrs(defaults, allow_mutable_defaults)
                | seq_typed_attrs(defaults, allow_mutable_defaults)
            )
    else:
        res = (
            bare_typed_attrs(defaults)
            | int_typed_attrs(defaults)
            | str_typed_attrs(defaults)
            | float_typed_attrs(defaults)
            | frozenset_typed_attrs(defaults)
            | homo_tuple_typed_attrs(defaults)
        )

        if not for_frozen:
            res = (
                res
                | dict_typed_attrs(defaults, allow_mutable_defaults)
                | new_dict_typed_attrs(defaults, allow_mutable_defaults)
                | set_typed_attrs(defaults, allow_mutable_defaults)
                | list_typed_attrs(defaults, allow_mutable_defaults)
                | mutable_seq_typed_attrs(defaults, allow_mutable_defaults)
                | seq_typed_attrs(defaults, allow_mutable_defaults)
            )

    return res


def _create_hyp_class(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[Tuple[Type, PosArgs]]:
    """
    A helper function for Hypothesis to generate attrs classes.

    The result is a tuple: an attrs class, and a tuple of values to
    instantiate it.
    """

    def key(t):
        return t[0]._default is not attr.NOTHING

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat)
    return tuples(
        just(
            make_class(
                "HypClass",
                OrderedDict(zip(gen_attr_names(), attrs)),
                frozen=frozen,
            )
        ),
        tuples(*vals),
    )


def _create_dataclass(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[Tuple[Type, PosArgs]]:
    """
    A helper function for Hypothesis to generate dataclasses.

    The result is a tuple: a dataclass, and a tuple of values to
    instantiate it.
    """

    def key(t):
        return t[0]._default is not attr.NOTHING

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat)
    return tuples(
        just(
            make_dataclass(
                "HypDataclass",
                [
                    (n, a.type)
                    if a._default is NOTHING
                    else (
                        (n, a.type, field(default=a._default))
                        if not isinstance(a._default, Factory)
                        else (
                            n,
                            a.type,
                            field(default_factory=a._default.factory),
                        )
                    )
                    for n, a in zip(gen_attr_names(), attrs)
                ],
                frozen=frozen,
            )
        ),
        tuples(*vals),
    )


def _create_hyp_class_and_strat(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArg]]],
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
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
        just(tuples(*vals)),
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
def dict_typed_attrs(
    draw, defaults=None, allow_mutable_defaults=True
) -> SearchStrategy[Tuple[_CountingAttr, SearchStrategy]]:
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.
    """
    default = attr.NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    return (attr.ib(type=Dict[str, int], default=default), val_strat)


@composite
def new_dict_typed_attrs(draw, defaults=None, allow_mutable_defaults=True):
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.

    Uses the new 3.9 dict annotation.
    """
    default_val = attr.NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    else:
        default = default_val

    type = (
        dict[str, int] if draw(booleans()) else dict
    )  # We also produce bare dicts.

    return (attr.ib(type=type, default=default), val_strat)


@composite
def set_typed_attrs(draw, defaults=None, allow_mutable_defaults=True):
    """
    Generate a tuple of an attribute and a strategy that yields sets
    for that attribute. The sets contain integers.
    """
    default_val = attr.NOTHING
    val_strat = sets(integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    else:
        default = default_val
    return (
        attr.ib(
            type=set[int]
            if draw(booleans())
            else (AbcSet[int] if draw(booleans()) else AbcMutableSet[int]),
            default=default,
        ),
        val_strat,
    )


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
            type=frozenset[int],
            default=default,
        ),
        val_strat,
    )


@composite
def list_typed_attrs(draw, defaults=None, allow_mutable_defaults=True):
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain floats.
    """
    default_val = attr.NOTHING
    val_strat = lists(floats(allow_infinity=False, allow_nan=False))
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    else:
        default = default_val
    return (
        attr.ib(
            type=list[float] if draw(booleans()) else List[float],
            default=default,
        ),
        val_strat,
    )


@composite
def seq_typed_attrs(draw, defaults=None, allow_mutable_defaults=True):
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain floats.
    """
    default_val = attr.NOTHING
    val_strat = lists(integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    else:
        default = default_val

    return (
        attr.ib(
            type=Sequence[int]
            if not is_39_or_later or draw(booleans())
            else AbcSequence[int],
            default=default,
        ),
        val_strat,
    )


@composite
def mutable_seq_typed_attrs(draw, defaults=None, allow_mutable_defaults=True):
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain floats.
    """
    default_val = attr.NOTHING
    val_strat = lists(floats(allow_infinity=False, allow_nan=False))
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    else:
        default = default_val

    return (
        attr.ib(
            type=MutableSequence[float]
            if not is_39_or_later
            else AbcMutableSequence[float],
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


def just_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs]
    ],
    defaults: PosArgs,
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: nested_cl(*defaults))
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=nested_cl, default=default),
            just(nested_cl(*nested_cl_args)),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def list_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs]
    ],
    defaults: PosArgs,
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: [nested_cl(*defaults)])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=List[nested_cl], default=default),
            just([nested_cl(*nested_cl_args)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def new_list_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs]
    ],
    defaults: PosArgs,
):
    """Uses the new 3.9 list type annotation."""
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: [nested_cl(*defaults)])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=list[nested_cl], default=default),
            just([nested_cl(*nested_cl_args)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def dict_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs]
    ],
    defaults: PosArgs,
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    default = attr.Factory(lambda: {"cls": nested_cl(*defaults)})
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=Dict[str, nested_cl], default=default),
            just({"cls": nested_cl(*nested_cl_args)}),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def _create_hyp_nested_strategy(
    simple_class_strategy: SearchStrategy,
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
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
    attrs_and_classes: SearchStrategy[
        Tuple[
            List[Tuple[_CountingAttr, PosArgs]],
            Tuple[Type, SearchStrategy[PosArgs]],
        ]
    ] = tuples(lists_of_typed_attrs(), simple_class_strategy)

    return nested_classes(attrs_and_classes)


@composite
def nested_classes(
    draw: Callable[[SearchStrategy[T]], T],
    attrs_and_classes: SearchStrategy[
        Tuple[
            List[Tuple[_CountingAttr, SearchStrategy]],
            Tuple[Type, SearchStrategy[PosArgs]],
        ]
    ],
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
    attrs, class_and_strat = draw(attrs_and_classes)
    cls, strat = class_and_strat
    defaults = tuple(draw(strat))
    init_vals = tuple(draw(strat))
    if is_39_or_later:
        return draw(
            list_of_class((attrs, (cls, init_vals)), defaults)
            | new_list_of_class((attrs, (cls, init_vals)), defaults)
            | dict_of_class((attrs, (cls, init_vals)), defaults)
            | just_class((attrs, (cls, init_vals)), defaults)
        )
    else:
        return draw(
            list_of_class((attrs, (cls, init_vals)), defaults)
            | dict_of_class((attrs, (cls, init_vals)), defaults)
            | just_class((attrs, (cls, init_vals)), defaults)
        )


def nested_typed_classes_and_strat(
    defaults=None, min_attrs=0
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
    return recursive(
        simple_typed_classes_and_strats(
            defaults=defaults, min_attrs=min_attrs
        ),
        _create_hyp_nested_strategy,
    )


@composite
def nested_typed_classes(draw, defaults=None, min_attrs=0):
    cl, strat = draw(
        nested_typed_classes_and_strat(defaults=defaults, min_attrs=min_attrs)
    )
    return cl, draw(strat)
