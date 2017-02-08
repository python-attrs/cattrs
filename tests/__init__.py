import string
import keyword

from enum import Enum
from typing import (Tuple, Sequence, MutableSequence, List, Dict,
                    MutableMapping, Mapping, Any)

import attr

from attr import make_class
from hypothesis import strategies as st

primitive_strategies = st.sampled_from([(st.integers(), int),
                                        (st.floats(allow_nan=False), float),
                                        (st.text(), str),
                                        (st.binary(), bytes)])


@st.composite
def enums_of_primitives(draw):
    """Generate enum classes with primitive values."""
    names = draw(st.sets(st.text(min_size=1), min_size=1))
    n = len(names)
    vals = draw(st.one_of(st.sets(st.one_of(
            st.integers(),
            st.floats(allow_nan=False),
            st.text(min_size=1)),
        min_size=n, max_size=n)))
    return Enum('HypEnum', list(zip(names, vals)))


list_types = st.sampled_from([List, Sequence, MutableSequence])


@st.composite
def lists_of_primitives(draw):
    """Generate a strategy that yields tuples of list of primitives and types.

    For example, a sample value might be ([1,2], List[int]).
    """
    prim_strat, t = draw(primitive_strategies)
    list_t = draw(list_types.map(lambda list_t: list_t[t]) | list_types)
    return draw(st.lists(prim_strat)), list_t


#lists_of_primitives = primitive_strategies.flatmap(
#    lambda e: st.tuples(st.lists(e[0]),
#                        st.one_of(
#                            list_types.map(lambda t: t[e[1]]), list_types)))

h_tuple_types = st.sampled_from([Tuple, Sequence])
h_tuples_of_primitives = primitive_strategies.flatmap(
    lambda e: st.tuples(st.lists(e[0]),
                        st.one_of(st.sampled_from([Tuple[e[1], ...],
                                                  Sequence[e[1]]]),
                        h_tuple_types))).map(lambda e: (tuple(e[0]), e[1]))

dict_types = st.sampled_from([Dict, MutableMapping, Mapping])

seqs_of_primitives = st.one_of(lists_of_primitives(), h_tuples_of_primitives)


def create_generic_dict_type(type1, type2):
    """Create a strategy for generating parameterized dict types."""
    return st.one_of(dict_types,
                     dict_types.map(lambda t: t[type1, type2]),
                     dict_types.map(lambda t: t[Any, type2]),
                     dict_types.map(lambda t: t[type1, Any]))


def create_dict_and_type(tuple_of_strats):
    """Map two primitive strategies into a strategy for dict and type."""
    (prim_strat_1, type_1), (prim_strat_2, type_2) = tuple_of_strats

    return st.tuples(st.dictionaries(prim_strat_1, prim_strat_2),
                     create_generic_dict_type(type_1, type_2))


dicts_of_primitives = (st.tuples(primitive_strategies, primitive_strategies)
                       .flatmap(create_dict_and_type))


def _gen_attr_names():
    """
    Generate names for attributes, 'a'...'z', then 'aa'...'zz'.
    ~702 different attribute names should be enough in practice.
    Some short strings (such as 'as') are keywords, so we skip them.
    """
    lc = string.ascii_lowercase
    for c in lc:
        yield c
    for outer in lc:
        for inner in lc:
            res = outer + inner
            if keyword.iskeyword(res):
                continue
            yield outer + inner


def _create_hyp_class(attrs):
    """
    A helper function for Hypothesis to generate attrs classes.
    """
    return make_class('HypClass', dict(zip(_gen_attr_names(), attrs)))


def _create_hyp_nested_strategy(simple_class_strategy):
    """
    Create a recursive attrs class.
    Given a strategy for building (simpler) classes, create and return
    a strategy for building classes that have as an attribute: either just
    the simpler class, a list of simpler classes, or a dict mapping the string
    "cls" to a simpler class.
    """
    # Use a tuple strategy to combine simple attributes and an attr class.
    def just_class(tup):
        combined_attrs = list(tup[0])
        combined_attrs.append(attr.ib(default=attr.Factory(tup[1])))
        return _create_hyp_class(combined_attrs)

    def list_of_class(tup):
        default = attr.Factory(lambda: [tup[1]()])
        combined_attrs = list(tup[0])
        combined_attrs.append(attr.ib(default=default))
        return _create_hyp_class(combined_attrs)

    def dict_of_class(tup):
        default = attr.Factory(lambda: {"cls": tup[1]()})
        combined_attrs = list(tup[0])
        combined_attrs.append(attr.ib(default=default))
        return _create_hyp_class(combined_attrs)

    # A strategy producing tuples of the form ([list of attributes], <given
    # class strategy>).
    attrs_and_classes = st.tuples(list_of_attrs, simple_class_strategy)

    return st.one_of(attrs_and_classes.map(just_class),
                     attrs_and_classes.map(list_of_class),
                     attrs_and_classes.map(dict_of_class))


bare_attrs = st.just(attr.ib(default=None))
int_attrs = st.integers().map(lambda i: attr.ib(default=i))
str_attrs = st.text().map(lambda s: attr.ib(default=s))
float_attrs = st.floats().map(lambda f: attr.ib(default=f))
dict_attrs = (st.dictionaries(keys=st.text(), values=st.integers())
              .map(lambda d: attr.ib(default=d)))

simple_attrs = st.one_of(bare_attrs, int_attrs, str_attrs, float_attrs,
                         dict_attrs)

# Python functions support up to 255 arguments.
list_of_attrs = st.lists(simple_attrs, average_size=9, max_size=50)
simple_classes = list_of_attrs.map(_create_hyp_class)

# Ok, so st.recursive works by taking a base strategy (in this case,
# simple_classes) and a special function. This function receives a strategy,
# and returns another strategy (building on top of the base strategy).
nested_classes = st.recursive(simple_classes, _create_hyp_nested_strategy)
