"""Strategies for attributes with types and classes using them."""
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
    Dict,
    FrozenSet,
    List,
    MutableSequence,
    MutableSet,
    NewType,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
)

import attr
from attr import NOTHING, Factory, frozen
from attr._make import _CountingAttr
from hypothesis import note
from hypothesis.strategies import (
    DrawFn,
    SearchStrategy,
    booleans,
    composite,
    dictionaries,
    fixed_dictionaries,
    floats,
    frozensets,
    integers,
    just,
    lists,
    recursive,
    sampled_from,
    sets,
    text,
    tuples,
)

from .untyped import gen_attr_names, make_class

is_39_or_later = sys.version_info[:2] >= (3, 9)
PosArg = Any
PosArgs = Tuple[PosArg]
KwArgs = Dict[str, Any]
T = TypeVar("T")


def simple_typed_classes(
    defaults=None, min_attrs=0, frozen=False, kw_only=None, newtypes=True
) -> SearchStrategy[Tuple[Type, PosArgs, KwArgs]]:
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        for_frozen=frozen,
        kw_only=kw_only,
        newtypes=newtypes,
    ).flatmap(partial(_create_hyp_class, frozen=frozen))


def simple_typed_dataclasses(defaults=None, min_attrs=0, frozen=False, newtypes=True):
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        for_frozen=frozen,
        allow_mutable_defaults=False,
        newtypes=newtypes,
    ).flatmap(partial(_create_dataclass, frozen=frozen))


def simple_typed_classes_and_strats(
    defaults=None, min_attrs=0, kw_only=None, newtypes=True
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    """Yield tuples of (class, (strategies))."""
    return lists_of_typed_attrs(
        defaults, min_size=min_attrs, kw_only=kw_only, newtypes=newtypes
    ).flatmap(_create_hyp_class_and_strat)


def lists_of_typed_attrs(
    defaults=None,
    min_size=0,
    for_frozen=False,
    allow_mutable_defaults=True,
    kw_only=None,
    newtypes=True,
) -> SearchStrategy[List[Tuple[_CountingAttr, SearchStrategy[PosArg]]]]:
    # Python functions support up to 255 arguments.
    return lists(
        simple_typed_attrs(
            defaults,
            for_frozen=for_frozen,
            allow_mutable_defaults=allow_mutable_defaults,
            kw_only=kw_only,
            newtypes=newtypes,
        ),
        min_size=min_size,
        max_size=50,
    ).map(
        lambda l: sorted(l, key=lambda t: (t[0]._default is not NOTHING, t[0].kw_only))
    )


def simple_typed_attrs(
    defaults=None,
    for_frozen=False,
    allow_mutable_defaults=True,
    kw_only=None,
    newtypes=True,
) -> SearchStrategy[Tuple[_CountingAttr, SearchStrategy[PosArgs]]]:
    if not is_39_or_later:
        res = (
            bare_typed_attrs(defaults, kw_only)
            | int_typed_attrs(defaults, kw_only)
            | str_typed_attrs(defaults, kw_only)
            | float_typed_attrs(defaults, kw_only)
            | frozenset_typed_attrs(defaults, legacy_types_only=True, kw_only=kw_only)
            | homo_tuple_typed_attrs(defaults, legacy_types_only=True, kw_only=kw_only)
        )
        if newtypes:
            res = (
                res
                | newtype_int_typed_attrs(defaults, kw_only)
                | newtype_attrs_typed_attrs(defaults, kw_only)
            )
        if not for_frozen:
            res = (
                res
                | dict_typed_attrs(defaults, allow_mutable_defaults, kw_only)
                | mutable_seq_typed_attrs(
                    defaults,
                    allow_mutable_defaults,
                    legacy_types_only=True,
                    kw_only=kw_only,
                )
                | seq_typed_attrs(
                    defaults,
                    allow_mutable_defaults,
                    legacy_types_only=True,
                    kw_only=kw_only,
                )
                | list_typed_attrs(
                    defaults,
                    allow_mutable_defaults,
                    legacy_types_only=True,
                    kw_only=kw_only,
                )
                | set_typed_attrs(
                    defaults,
                    allow_mutable_defaults,
                    legacy_types_only=True,
                    kw_only=kw_only,
                )
            )
    else:
        res = (
            bare_typed_attrs(defaults, kw_only)
            | int_typed_attrs(defaults, kw_only)
            | str_typed_attrs(defaults, kw_only)
            | float_typed_attrs(defaults, kw_only)
            | frozenset_typed_attrs(defaults, kw_only=kw_only)
            | homo_tuple_typed_attrs(defaults, kw_only=kw_only)
        )
        if newtypes:
            res = (
                res
                | newtype_int_typed_attrs(defaults, kw_only)
                | newtype_attrs_typed_attrs(defaults, kw_only)
            )

        if not for_frozen:
            res = (
                res
                | dict_typed_attrs(defaults, allow_mutable_defaults, kw_only)
                | new_dict_typed_attrs(defaults, allow_mutable_defaults, kw_only)
                | set_typed_attrs(defaults, allow_mutable_defaults, kw_only=kw_only)
                | list_typed_attrs(defaults, allow_mutable_defaults, kw_only=kw_only)
                | mutable_seq_typed_attrs(
                    defaults, allow_mutable_defaults, kw_only=kw_only
                )
                | seq_typed_attrs(defaults, allow_mutable_defaults, kw_only=kw_only)
            )

    return res


def _create_hyp_class(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[Tuple[Type, PosArgs, KwArgs]]:
    """
    A helper function for Hypothesis to generate attrs classes.

    The result is a tuple: an attrs class, tuple of values to
    instantiate it, and a kwargs dict for kw_only args.
    """

    def key(t):
        return (t[0]._default is not attr.NOTHING, t[0].kw_only)

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat if not a[0].kw_only)
    note(f"Class fields: {attrs}")
    attrs_dict = OrderedDict(zip(gen_attr_names(), attrs))
    kwarg_strats = {}
    for attr_name, attr_and_strat in zip(gen_attr_names(), attrs_and_strat):
        if attr_and_strat[0].kw_only:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            kwarg_strats[attr_name] = attr_and_strat[1]

    return tuples(
        just(make_class("HypAttrsClass", attrs_dict, frozen=frozen)),
        tuples(*vals),
        fixed_dictionaries(kwarg_strats),
    )


def _create_dataclass(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[Tuple[Type, PosArgs, KwArgs]]:
    """
    A helper function for Hypothesis to generate dataclasses.

    The result is a tuple: a dataclass, a tuple of values to
    instantiate it, and an empty dict (usually used for kw-only attrs attributes).
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
                        else (n, a.type, field(default_factory=a._default.factory))
                    )
                    for n, a in zip(gen_attr_names(), attrs)
                ],
                frozen=frozen,
            )
        ),
        tuples(*vals),
        just({}),
    )


def _create_hyp_class_and_strat(
    attrs_and_strategy: List[Tuple[_CountingAttr, SearchStrategy[PosArg]]]
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    def key(t):
        return (t[0].default is not attr.NOTHING, t[0].kw_only)

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat if not a[0].kw_only)
    kwarg_strats = {}
    for attr_name, attr_and_strat in zip(gen_attr_names(), attrs_and_strat):
        if attr_and_strat[0].kw_only:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            kwarg_strats[attr_name] = attr_and_strat[1]
    return tuples(
        just(make_class("HypClass", OrderedDict(zip(gen_attr_names(), attrs)))),
        just(tuples(*vals)),
        just(fixed_dictionaries(kwarg_strats)),
    )


@composite
def bare_typed_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields values
    appropriate for that attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = None
    return (
        attr.ib(
            type=Any,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        just(None),
    )


@composite
def int_typed_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields ints for that
    attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(integers())
    return (
        attr.ib(
            type=int,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        integers(),
    )


@composite
def str_typed_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields strs for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(text())
    return (
        attr.ib(
            type=str,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        text(),
    )


@composite
def float_typed_attrs(draw, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields floats for that
    attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(floats())
    return (
        attr.ib(
            type=float,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        floats(),
    )


@composite
def dict_typed_attrs(
    draw, defaults=None, allow_mutable_defaults=True, kw_only=None
) -> SearchStrategy[Tuple[_CountingAttr, SearchStrategy]]:
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.
    The generated dict types are what's expected to be used on pre-3.9 Pythons.
    """
    default = attr.NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    type = draw(sampled_from([Dict[str, int], Dict, dict]))
    return (
        attr.ib(
            type=type,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def new_dict_typed_attrs(
    draw, defaults=None, allow_mutable_defaults=True, kw_only=None
):
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

    return (
        attr.ib(
            type=dict[str, int],
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def set_typed_attrs(
    draw: DrawFn,
    defaults=None,
    allow_mutable_defaults=True,
    legacy_types_only=False,
    kw_only=None,
):
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

    type = draw(
        sampled_from(
            [set, set[int], AbcSet[int], AbcMutableSet[int]]
            if not legacy_types_only
            else [set, Set[int], MutableSet[int]]
        )
    )
    return (
        attr.ib(
            type=type,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def frozenset_typed_attrs(
    draw: DrawFn, defaults=None, legacy_types_only=False, kw_only=None
):
    """
    Generate a tuple of an attribute and a strategy that yields frozensets
    for that attribute. The frozensets contain integers.
    """
    default = attr.NOTHING
    val_strat = frozensets(integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    type = draw(
        sampled_from(
            [frozenset[int], frozenset, FrozenSet[int], FrozenSet]
            if not legacy_types_only
            else [frozenset, FrozenSet[int], FrozenSet]
        )
    )
    return (
        attr.ib(
            type=type,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def list_typed_attrs(
    draw: DrawFn,
    defaults=None,
    allow_mutable_defaults=True,
    legacy_types_only=False,
    kw_only=None,
):
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
            type=draw(
                sampled_from(
                    [list[float], list, List[float], List]
                    if not legacy_types_only
                    else [List, List[float], list]
                )
            ),
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def seq_typed_attrs(
    draw,
    defaults=None,
    allow_mutable_defaults=True,
    legacy_types_only=False,
    kw_only=None,
):
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain integers.
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
            type=AbcSequence[int] if not legacy_types_only else Sequence[int],
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def mutable_seq_typed_attrs(
    draw,
    defaults=None,
    allow_mutable_defaults=True,
    legacy_types_only=False,
    kw_only=None,
):
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
            type=AbcMutableSequence[float]
            if not legacy_types_only
            else MutableSequence[float],
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def homo_tuple_typed_attrs(draw, defaults=None, legacy_types_only=False, kw_only=None):
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
            type=draw(
                sampled_from(
                    [tuple[str, ...], tuple, Tuple, Tuple[str, ...]]
                    if not legacy_types_only
                    else [tuple, Tuple, Tuple[str, ...]]
                )
            ),
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        val_strat,
    )


@composite
def newtype_int_typed_attrs(draw: DrawFn, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields ints for that
    attribute.
    """
    default = attr.NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(integers())
    type = NewType("NewInt", int)
    return (
        attr.ib(
            type=type,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        integers(),
    )


@composite
def newtype_attrs_typed_attrs(draw: DrawFn, defaults=None, kw_only=None):
    """
    Generate a tuple of an attribute and a strategy that yields values for that
    attribute.
    """
    default = attr.NOTHING

    @frozen
    class NewTypeAttrs:
        a: int

    if defaults is True or (defaults is None and draw(booleans())):
        default = NewTypeAttrs(draw(integers()))

    type = NewType("NewAttrs", NewTypeAttrs)
    return (
        attr.ib(
            type=type,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        integers().map(NewTypeAttrs),
    )


def just_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs, KwArgs]
    ],
    defaults: Tuple[PosArgs, KwArgs],
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = attr.Factory(lambda: nested_cl(*defaults[0], **defaults[1]))
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=nested_cl, default=default),
            just(nested_cl(*nested_cl_args, **nested_cl_kwargs)),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def list_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs, KwArgs]
    ],
    defaults: Tuple[PosArgs, KwArgs],
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = attr.Factory(lambda: [nested_cl(*defaults[0], **defaults[1])])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=List[nested_cl], default=default),
            just([nested_cl(*nested_cl_args, **nested_cl_kwargs)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def new_list_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs, KwArgs]
    ],
    defaults: Tuple[PosArgs, KwArgs],
):
    """Uses the new 3.9 list type annotation."""
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = attr.Factory(lambda: [nested_cl(*defaults[0], **defaults[1])])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=list[nested_cl], default=default),
            just([nested_cl(*nested_cl_args, **nested_cl_kwargs)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def dict_of_class(
    tup: Tuple[
        List[Tuple[_CountingAttr, SearchStrategy]], Tuple[Type, PosArgs, KwArgs]
    ],
    defaults: Tuple[PosArgs, KwArgs],
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = attr.Factory(lambda: {"cls": nested_cl(*defaults[0], **defaults[1])})
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            attr.ib(type=Dict[str, nested_cl], default=default),
            just({"cls": nested_cl(*nested_cl_args, **nested_cl_kwargs)}),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def _create_hyp_nested_strategy(
    simple_class_strategy: SearchStrategy, kw_only=None, newtypes=True
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
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
            List[Tuple[_CountingAttr, PosArgs]], Tuple[Type, SearchStrategy[PosArgs]],
        ]
    ] = tuples(
        lists_of_typed_attrs(kw_only=kw_only, newtypes=newtypes), simple_class_strategy
    )

    return nested_classes(attrs_and_classes)


@composite
def nested_classes(
    draw: DrawFn,
    attrs_and_classes: SearchStrategy[
        Tuple[
            List[Tuple[_CountingAttr, SearchStrategy]],
            Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]],
        ]
    ],
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    attrs, class_and_strat = draw(attrs_and_classes)
    cls, strat, kw_strat = class_and_strat
    pos_defs = tuple(draw(strat))
    kwarg_defs = draw(kw_strat)
    init_vals = tuple(draw(strat))
    init_kwargs = draw(kw_strat)
    if is_39_or_later:
        return draw(
            list_of_class(
                (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
            )
            | new_list_of_class(
                (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
            )
            | dict_of_class(
                (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
            )
            | just_class((attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs))
        )
    else:
        return draw(
            list_of_class(
                (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
            )
            | dict_of_class(
                (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
            )
            | just_class((attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs))
        )


def nested_typed_classes_and_strat(
    defaults=None, min_attrs=0, kw_only=None, newtypes=True
) -> SearchStrategy[Tuple[Type, SearchStrategy[PosArgs]]]:
    return recursive(
        simple_typed_classes_and_strats(
            defaults=defaults, min_attrs=min_attrs, kw_only=kw_only, newtypes=newtypes
        ),
        partial(_create_hyp_nested_strategy, kw_only=kw_only, newtypes=newtypes),
        max_leaves=20,
    )


@composite
def nested_typed_classes(draw, defaults=None, min_attrs=0, kw_only=None, newtypes=True):
    cl, strat, kwarg_strat = draw(
        nested_typed_classes_and_strat(
            defaults=defaults, min_attrs=min_attrs, kw_only=kw_only, newtypes=newtypes
        )
    )
    return cl, draw(strat), draw(kwarg_strat)
