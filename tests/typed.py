"""Strategies for attributes with types and classes using them."""

from collections.abc import MutableSequence as AbcMutableSequence
from collections.abc import MutableSet as AbcMutableSet
from collections.abc import Sequence as AbcSequence
from collections.abc import Set as AbcSet
from dataclasses import field as dc_field
from dataclasses import make_dataclass
from functools import partial
from pathlib import Path
from typing import (
    Any,
    Dict,
    Final,
    FrozenSet,
    List,
    MutableSequence,
    MutableSet,
    NewType,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
)

from attr._make import _CountingAttr
from attrs import NOTHING, AttrsInstance, Factory, field, frozen
from hypothesis import note
from hypothesis.strategies import (
    DrawFn,
    SearchStrategy,
    booleans,
    characters,
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

PosArg = Any
PosArgs = tuple[PosArg]
KwArgs = dict[str, Any]
T = TypeVar("T")


def simple_typed_classes(
    defaults=None,
    min_attrs=0,
    frozen=False,
    kw_only=None,
    newtypes=True,
    text_codec: str = "utf8",
    allow_infinity=None,
    allow_nan=True,
) -> SearchStrategy[tuple[type, PosArgs, KwArgs]]:
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        for_frozen=frozen,
        kw_only=kw_only,
        newtypes=newtypes,
        text_codec=text_codec,
        allow_infinity=allow_infinity,
        allow_nan=allow_nan,
    ).flatmap(partial(_create_hyp_class, frozen=frozen))


def simple_typed_dataclasses(
    defaults=None, min_attrs=0, frozen=False, newtypes=True, allow_nan=True
):
    """Yield tuples of (class, values)."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        for_frozen=frozen,
        allow_mutable_defaults=False,
        newtypes=newtypes,
        allow_nan=allow_nan,
    ).flatmap(partial(_create_dataclass, frozen=frozen))


def simple_typed_classes_and_strats(
    defaults=None, min_attrs=0, kw_only=None, newtypes=True, allow_nan=True
) -> SearchStrategy[tuple[type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    """Yield tuples of (class, (strategies))."""
    return lists_of_typed_attrs(
        defaults,
        min_size=min_attrs,
        kw_only=kw_only,
        newtypes=newtypes,
        allow_nan=allow_nan,
    ).flatmap(_create_hyp_class_and_strat)


def lists_of_typed_attrs(
    defaults=None,
    min_size=0,
    for_frozen=False,
    allow_mutable_defaults=True,
    kw_only=None,
    newtypes=True,
    text_codec="utf8",
    allow_infinity=None,
    allow_nan=True,
) -> SearchStrategy[list[tuple[_CountingAttr, SearchStrategy[PosArg]]]]:
    # Python functions support up to 255 arguments.
    return lists(
        simple_typed_attrs(
            defaults,
            for_frozen=for_frozen,
            allow_mutable_defaults=allow_mutable_defaults,
            kw_only=kw_only,
            newtypes=newtypes,
            text_codec=text_codec,
            allow_infinity=allow_infinity,
            allow_nan=allow_nan,
        ),
        min_size=min_size,
        max_size=50,
    ).map(
        lambda lst: sorted(
            lst, key=lambda t: (t[0]._default is not NOTHING, t[0].kw_only)
        )
    )


def simple_typed_attrs(
    defaults=None,
    for_frozen=False,
    allow_mutable_defaults=True,
    kw_only=None,
    newtypes=True,
    text_codec="utf8",
    allow_infinity=None,
    allow_nan=True,
) -> SearchStrategy[tuple[_CountingAttr, SearchStrategy[PosArgs]]]:
    res = (
        any_typed_attrs(defaults, kw_only)
        | int_typed_attrs(defaults, kw_only)
        | str_typed_attrs(defaults, kw_only, text_codec)
        | float_typed_attrs(defaults, kw_only, allow_infinity, allow_nan)
        | frozenset_typed_attrs(defaults, kw_only=kw_only)
        | homo_tuple_typed_attrs(defaults, kw_only=kw_only)
        | path_typed_attrs(defaults, kw_only=kw_only)
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
            | mutable_seq_typed_attrs(defaults, allow_mutable_defaults, kw_only=kw_only)
            | seq_typed_attrs(defaults, allow_mutable_defaults, kw_only=kw_only)
        )

    return res


def _create_hyp_class(
    attrs_and_strategy: list[tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[tuple[type, PosArgs, KwArgs]]:
    """
    A helper function for Hypothesis to generate attrs classes.

    The result is a tuple: an attrs class, tuple of values to
    instantiate it, and a kwargs dict for kw_only args.
    """

    def key(t):
        return (t[0]._default is not NOTHING, t[0].kw_only)

    attrs_and_strat = sorted(attrs_and_strategy, key=key)
    attrs = [a[0] for a in attrs_and_strat]
    for i, a in enumerate(attrs):
        a.counter = i
    vals = tuple((a[1]) for a in attrs_and_strat if not a[0].kw_only)
    note(f"Class fields: {attrs}")
    attrs_dict = {}

    names = gen_attr_names()
    kwarg_strats = {}

    for ix, (attribute, strat) in enumerate(attrs_and_strat):
        name = next(names)
        attrs_dict[name] = attribute
        if ix % 2 == 1:
            # Every third attribute gets an alias, the next attribute name.
            alias = next(names)
            attribute.alias = alias
            name = alias
        else:
            # No alias.
            if name[0] == "_":
                name = name[1:]

        if attribute.kw_only:
            kwarg_strats[name] = strat
    note(f"Attributes: {attrs_dict}")

    return tuples(
        just(make_class("HypAttrsClass", attrs_dict, frozen=frozen)),
        tuples(*vals),
        fixed_dictionaries(kwarg_strats),
    )


def _create_dataclass(
    attrs_and_strategy: list[tuple[_CountingAttr, SearchStrategy[PosArgs]]],
    frozen=False,
) -> SearchStrategy[tuple[Type, PosArgs, KwArgs]]:
    """
    A helper function for Hypothesis to generate dataclasses.

    The result is a tuple: a dataclass, a tuple of values to
    instantiate it, and an empty dict (usually used for kw-only attrs attributes).
    """

    def key(t):
        return t[0]._default is not NOTHING

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
                    (
                        (n, a.type)
                        if a._default is NOTHING
                        else (
                            (n, a.type, dc_field(default=a._default))
                            if not isinstance(a._default, Factory)
                            else (
                                n,
                                a.type,
                                dc_field(default_factory=a._default.factory),
                            )
                        )
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
    attrs_and_strategy: list[tuple[_CountingAttr, SearchStrategy[PosArg]]]
) -> SearchStrategy[tuple[type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    def key(t):
        return (t[0].default is not NOTHING, t[0].kw_only)

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
        just(make_class("HypClass", dict(zip(gen_attr_names(), attrs)))),
        just(tuples(*vals)),
        just(fixed_dictionaries(kwarg_strats)),
    )


@composite
def any_typed_attrs(
    draw: DrawFn, defaults=None, kw_only=None
) -> tuple[_CountingAttr, SearchStrategy[None]]:
    """Attributes typed as `Any`, having values of `None`."""
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = None
    return (
        field(
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
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(integers())
    return (
        field(
            type=int,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        integers(),
    )


@composite
def str_typed_attrs(draw, defaults=None, kw_only=None, codec: str = "utf8"):
    """
    Generate a tuple of an attribute and a strategy that yields strs for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(text())
    return (
        field(
            type=str,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        text(characters(codec=codec)),
    )


@composite
def float_typed_attrs(
    draw, defaults=None, kw_only=None, allow_infinity=None, allow_nan=True
):
    """
    Generate a tuple of an attribute and a strategy that yields floats for that
    attribute.
    """
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(floats(allow_infinity=allow_infinity, allow_nan=allow_nan))
    return (
        field(
            type=float,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        floats(allow_infinity=allow_infinity, allow_nan=allow_nan),
    )


@composite
def path_typed_attrs(
    draw: DrawFn, defaults: Optional[bool] = None, kw_only: Optional[bool] = None
) -> tuple[_CountingAttr, SearchStrategy[Path]]:
    """
    Generate a tuple of an attribute and a strategy that yields paths for that
    attribute.
    """
    from string import ascii_lowercase

    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = Path(draw(text(ascii_lowercase, min_size=1)))
    return (
        field(
            type=Path,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        text(ascii_lowercase, min_size=1).map(Path),
    )


@composite
def dict_typed_attrs(
    draw: DrawFn, defaults=None, allow_mutable_defaults=True, kw_only=None
) -> tuple[_CountingAttr, SearchStrategy[dict[str, int]]]:
    """
    Generate a tuple of an attribute and a strategy that yields dictionaries
    for that attribute. The dictionaries map strings to integers.
    The generated dict types are what's expected to be used on pre-3.9 Pythons.
    """
    default = NOTHING
    val_strat = dictionaries(keys=text(), values=integers())
    if defaults is True or (defaults is None and draw(booleans())):
        default_val = draw(val_strat)
        if not allow_mutable_defaults or draw(booleans()):
            default = Factory(lambda: default_val)
        else:
            default = default_val
    type = draw(sampled_from([Dict[str, int], Dict, dict]))
    return (
        field(
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
    default_val = NOTHING
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
        field(
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
    default_val = NOTHING
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
        field(
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
    default = NOTHING
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
        field(
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
) -> tuple[_CountingAttr, SearchStrategy[list[float]]]:
    """
    Generate a tuple of an attribute and a strategy that yields lists
    for that attribute. The lists contain floats.
    """
    default_val = NOTHING
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
        field(
            type=draw(
                sampled_from(
                    [list[float], list, List[float], List, Final[list[float]]]
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
    default_val = NOTHING
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
        field(
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
    default_val = NOTHING
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
        field(
            type=(
                AbcMutableSequence[float]
                if not legacy_types_only
                else MutableSequence[float]
            ),
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
    default = NOTHING
    val_strat = tuples(text(), text(), text())
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(val_strat)
    return (
        field(
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
    default = NOTHING
    if defaults is True or (defaults is None and draw(booleans())):
        default = draw(integers())
    NewInt = NewType("NewInt", int)
    return (
        field(
            type=NewInt,
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
    default = NOTHING

    @frozen
    class NewTypeAttrs:
        a: int

    if defaults is True or (defaults is None and draw(booleans())):
        default = NewTypeAttrs(draw(integers()))

    NewAttrs = NewType("NewAttrs", NewTypeAttrs)
    return (
        field(
            type=NewAttrs,
            default=default,
            kw_only=draw(booleans()) if kw_only is None else kw_only,
        ),
        integers().map(NewTypeAttrs),
    )


def just_class(
    tup: tuple[
        list[tuple[_CountingAttr, SearchStrategy]], tuple[Type, PosArgs, KwArgs]
    ],
    defaults: tuple[PosArgs, KwArgs],
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = Factory(lambda: nested_cl(*defaults[0], **defaults[1]))
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            field(type=nested_cl, default=default),
            just(nested_cl(*nested_cl_args, **nested_cl_kwargs)),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def list_of_class(
    tup: tuple[
        list[tuple[_CountingAttr, SearchStrategy]], tuple[type, PosArgs, KwArgs]
    ],
    defaults: tuple[PosArgs, KwArgs],
) -> SearchStrategy[tuple[type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = Factory(lambda: [nested_cl(*defaults[0], **defaults[1])])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            field(type=List[nested_cl], default=default),
            just([nested_cl(*nested_cl_args, **nested_cl_kwargs)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def new_list_of_class(
    tup: tuple[
        list[tuple[_CountingAttr, SearchStrategy]], tuple[Type, PosArgs, KwArgs]
    ],
    defaults: tuple[PosArgs, KwArgs],
):
    """Uses the new 3.9 list type annotation."""
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = Factory(lambda: [nested_cl(*defaults[0], **defaults[1])])
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            field(type=list[nested_cl], default=default),
            just([nested_cl(*nested_cl_args, **nested_cl_kwargs)]),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def dict_of_class(
    tup: tuple[
        list[tuple[_CountingAttr, SearchStrategy]], tuple[Type, PosArgs, KwArgs]
    ],
    defaults: tuple[PosArgs, KwArgs],
):
    nested_cl = tup[1][0]
    nested_cl_args = tup[1][1]
    nested_cl_kwargs = tup[1][2]
    default = Factory(lambda: {"cls": nested_cl(*defaults[0], **defaults[1])})
    combined_attrs = list(tup[0])
    combined_attrs.append(
        (
            field(type=Dict[str, nested_cl], default=default),
            just({"cls": nested_cl(*nested_cl_args, **nested_cl_kwargs)}),
        )
    )
    return _create_hyp_class_and_strat(combined_attrs)


def _create_hyp_nested_strategy(
    simple_class_strategy: SearchStrategy, kw_only=None, newtypes=True, allow_nan=True
) -> SearchStrategy[tuple[type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]]]:
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
        tuple[list[tuple[_CountingAttr, PosArgs]], tuple[type, SearchStrategy[PosArgs]]]
    ] = tuples(
        lists_of_typed_attrs(kw_only=kw_only, newtypes=newtypes, allow_nan=allow_nan),
        simple_class_strategy,
    )

    return nested_classes(attrs_and_classes)


@composite
def nested_classes(
    draw: DrawFn,
    attrs_and_classes: SearchStrategy[
        tuple[
            list[tuple[_CountingAttr, SearchStrategy]],
            tuple[type, SearchStrategy[PosArgs], SearchStrategy[KwArgs]],
        ]
    ],
) -> tuple[type[AttrsInstance], SearchStrategy[PosArgs], SearchStrategy[KwArgs]]:
    attrs, class_and_strat = draw(attrs_and_classes)
    cls, strat, kw_strat = class_and_strat
    pos_defs = tuple(draw(strat))
    kwarg_defs = draw(kw_strat)
    init_vals = tuple(draw(strat))
    init_kwargs = draw(kw_strat)
    return draw(
        list_of_class((attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs))
        | new_list_of_class(
            (attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs)
        )
        | dict_of_class((attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs))
        | just_class((attrs, (cls, init_vals, init_kwargs)), (pos_defs, kwarg_defs))
    )


def nested_typed_classes_and_strat(
    defaults=None, min_attrs=0, kw_only=None, newtypes=True, allow_nan=True
) -> SearchStrategy[tuple[type, SearchStrategy[PosArgs]]]:
    return recursive(
        simple_typed_classes_and_strats(
            defaults=defaults,
            min_attrs=min_attrs,
            kw_only=kw_only,
            newtypes=newtypes,
            allow_nan=allow_nan,
        ),
        partial(
            _create_hyp_nested_strategy,
            kw_only=kw_only,
            newtypes=newtypes,
            allow_nan=allow_nan,
        ),
        max_leaves=20,
    )


@composite
def nested_typed_classes(
    draw: DrawFn,
    defaults=None,
    min_attrs=0,
    kw_only=None,
    newtypes=True,
    allow_nan=True,
):
    cl, strat, kwarg_strat = draw(
        nested_typed_classes_and_strat(
            defaults=defaults,
            min_attrs=min_attrs,
            kw_only=kw_only,
            newtypes=newtypes,
            allow_nan=allow_nan,
        )
    )
    return cl, draw(strat), draw(kwarg_strat)
