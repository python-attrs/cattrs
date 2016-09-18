"""Test loading functionality."""
from enum import Enum
from typing import (List, Sequence, MutableSequence, Tuple, Any, Set,
                    MutableSet, FrozenSet, MutableMapping, Mapping, Dict,
                    Optional, Union)

from pytest import raises

from hypothesis import given
from hypothesis.strategies import (integers, floats, text, one_of,
                                   sampled_from, lists, tuples, sets,
                                   frozensets, just, binary, dictionaries,
                                   composite, choices)

from cattr import Converter

primitive_strategies = sampled_from([(integers(), int),
                                     (floats(allow_nan=False), float),
                                     (text(), str)])

ints_and_type = tuples(integers(), just(int))
floats_and_type = tuples(floats(allow_nan=False), just(float))
strs_and_type = tuples(text(), just(str))
bytes_and_type = tuples(binary(), just(bytes))

primitives_and_type = one_of(ints_and_type, floats_and_type, strs_and_type,
                             bytes_and_type)

list_types = sampled_from([List, Sequence, MutableSequence])
mut_set_types = sampled_from([Set, MutableSet])
set_types = one_of(mut_set_types, just(FrozenSet))
dict_types = sampled_from([Dict, MutableMapping, Mapping])

lists_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(lists(e[0]),
                     one_of(list_types.map(lambda t: t[e[1]]), list_types)))

h_tuple_types = sampled_from([Tuple, Sequence])
h_tuples_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(lists(e[0]),
                     one_of(sampled_from([Tuple[e[1], ...], Sequence[e[1]]]),
                            h_tuple_types))).map(
    lambda e: (tuple(e[0]), e[1]))

seqs_of_primitives = one_of(lists_of_primitives, h_tuples_of_primitives)


@composite
def enums_of_primitives(draw):
    names = draw(sets(text(min_size=1), min_size=1))
    n = len(names)
    vals = draw(one_of(sets(one_of(
            integers(),
            floats(allow_nan=False),
            text(min_size=1)),
        min_size=n, max_size=n)))
    return Enum('HypEnum', list(zip(names, vals)))


def create_generic_type(generic_types, param_type):
    """Create a strategy for generating parameterized generic types."""
    return one_of(generic_types,
                  generic_types.map(lambda t: t[Any]),
                  generic_types.map(lambda t: t[param_type]))

mut_sets_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(sets(e[0]), create_generic_type(mut_set_types, e[1]))
)

frozen_sets_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(frozensets(e[0]), create_generic_type(just(FrozenSet),
                                                           e[1]))
)

sets_of_primitives = one_of(mut_sets_of_primitives, frozen_sets_of_primitives)


def create_generic_dict_type(type1, type2):
    """Create a strategy for generating parameterized dict types."""
    return one_of(dict_types,
                  dict_types.map(lambda t: t[type1, type2]),
                  dict_types.map(lambda t: t[Any, type2]),
                  dict_types.map(lambda t: t[type1, Any]))


def create_dict_and_type(tuple_of_strats):
    """Map two primitive strategies into a strategy for dict and type."""
    (prim_strat_1, type_1), (prim_strat_2, type_2) = tuple_of_strats

    return tuples(dictionaries(prim_strat_1, prim_strat_2),
                  create_generic_dict_type(type_1, type_2))


dicts_of_primitives = (tuples(primitive_strategies, primitive_strategies)
                       .flatmap(create_dict_and_type))


@given(primitives_and_type)
def test_loading_primitives(converter: Converter, primitive_and_type):
    """Test just loading a primitive value."""
    val, t = primitive_and_type
    assert converter.loads(val, t) == val
    assert converter.loads(val, Any) == val


@given(seqs_of_primitives)
def test_loading_seqs(converter: Converter, seq_and_type):
    """Test loading sequence generic types."""
    iterable, t = seq_and_type
    converted = converter.loads(iterable, t)
    for x, y in zip(iterable, converted):
        assert x == y


@given(sets_of_primitives, set_types)
def test_loading_sets(converter: Converter, set_and_type, set_type):
    """Test loading generic sets."""
    set_, input_set_type = set_and_type

    if input_set_type.__args__:
        set_type = set_type[input_set_type.__args__[0]]

    converted = converter.loads(set_, set_type)
    assert converted == set_
    assert isinstance(converted, set_type)

    converted = converter.loads(set_, Any)
    assert converted == set_
    assert isinstance(converted, type(set_))


@given(sets_of_primitives)
def test_stringifying_sets(converter: Converter, set_and_type):
    """Test loading generic sets and converting the contents to str."""
    set_, input_set_type = set_and_type

    input_set_type.__args__ = (str,)
    converted = converter.loads(set_, input_set_type)
    assert len(converted) == len(set_)
    for e in set_:
        assert str(e) in converted


@given(lists(primitives_and_type))
def test_loading_hetero_tuples(converter: Converter, list_of_vals_and_types):
    """Test loading heterogenous tuples."""
    types = tuple(e[1] for e in list_of_vals_and_types)
    vals = [e[0] for e in list_of_vals_and_types]
    t = Tuple[types]

    converted = converter.loads(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert x == y

    for x, y in zip(types, converted):
        assert isinstance(y, x)


@given(lists(primitives_and_type))
def test_stringifying_tuples(converter: Converter, list_of_vals_and_types):
    """Stringify all elements of a heterogeneous tuple."""
    vals = [e[0] for e in list_of_vals_and_types]
    t = Tuple[(str,) * len(list_of_vals_and_types)]

    converted = converter.loads(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert str(x) == y

    for x in converted:
        assert isinstance(x, str)


@given(dicts_of_primitives)
def test_loading_dicts(converter: Converter, dict_and_type):
    d, t = dict_and_type

    converted = converter.loads(d, t)

    assert converted == d
    assert converted is not d


@given(dicts_of_primitives)
def test_stringifying_dicts(converter: Converter, dict_and_type):
    d, t = dict_and_type

    converted = converter.loads(d, Dict[str, str])

    for k, v in d.items():
        assert converted[str(k)] == str(v)


@given(primitives_and_type)
def test_loading_optional_primitives(converter: Converter, primitive_and_type):
    """Test loading Optional primitive types."""
    val, type = primitive_and_type

    assert converter.loads(val, Optional[type]) == val
    assert converter.loads(None, Optional[type]) is None


@given(lists_of_primitives)
def test_loading_lists_of_opt(converter: Converter, list_and_type):
    """Test loading Optional primitive types."""
    l, t = list_and_type

    l.append(None)
    args = t.__args__

    if args and args[0] not in (Any, str, Optional):
        with raises(TypeError):
            converter.loads(l, t)
    if args:
        optional_t = Optional[args[0]]
    else:
        optional_t = Optional
    t.__args__ = (optional_t, )

    converted = converter.loads(l, t)

    for x, y in zip(l, converted):
        assert x == y

    t.__args__ = args


@given(lists_of_primitives)
def test_stringifying_lists_of_opt(converter: Converter, list_and_type):
    """Test loading Optional primitive types into strings."""
    l, t = list_and_type

    l.append(None)

    converted = converter.loads(l, List[Optional[str]])

    for x, y in zip(l, converted):
        if x is None:
            assert x is y
        else:
            assert str(x) == y


@given(lists(integers()))
def test_loading_primitive_union_hook(converter: Converter, ints):
    """Test registering a union loading hook."""

    def load_hook(cl, val):
        """Even ints are passed through, odd are stringified."""
        return val if val % 2 == 0 else str(val)

    converter.register_loads_hook(Union[str, int], load_hook)

    converted = converter.loads(ints, List[Union[str, int]])

    for x, y in zip(ints, converted):
        if x % 2 == 0:
            assert x == y
        else:
            assert str(x) == y


@given(choices(), enums_of_primitives())
def test_loading_enums(converter: Converter, choice, enum):
    """Test loading enums by their values."""
    val = choice(list(enum))

    assert converter.loads(val.value, enum) == val
