"""Test structuring of collections and primitives."""
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Union,
)

from hypothesis import assume, given
from hypothesis.strategies import (
    binary,
    booleans,
    data,
    floats,
    frozensets,
    integers,
    just,
    lists,
    one_of,
    sampled_from,
    sets,
    text,
    tuples,
)
from pytest import raises

from cattr import Converter
from cattr._compat import is_bare, is_union_type
from cattr.converters import NoneType

from . import (
    dicts_of_primitives,
    enums_of_primitives,
    lists_of_primitives,
    primitive_strategies,
    seqs_of_primitives,
)
from ._compat import change_type_param

ints_and_type = tuples(integers(), just(int))
floats_and_type = tuples(floats(allow_nan=False), just(float))
strs_and_type = tuples(text(), just(str))
bytes_and_type = tuples(binary(), just(bytes))

primitives_and_type = one_of(
    ints_and_type, floats_and_type, strs_and_type, bytes_and_type
)

mut_set_types = sampled_from([Set, MutableSet])
set_types = one_of(mut_set_types, just(FrozenSet))


def create_generic_type(generic_types, param_type):
    """Create a strategy for generating parameterized generic types."""
    return one_of(
        generic_types,
        generic_types.map(lambda t: t[Any]),
        generic_types.map(lambda t: t[param_type]),
    )


mut_sets_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(sets(e[0]), create_generic_type(mut_set_types, e[1]))
)

frozen_sets_of_primitives = primitive_strategies.flatmap(
    lambda e: tuples(
        frozensets(e[0]), create_generic_type(just(FrozenSet), e[1])
    )
)

sets_of_primitives = one_of(mut_sets_of_primitives, frozen_sets_of_primitives)


@given(primitives_and_type)
def test_structuring_primitives(converter, primitive_and_type):
    # type: (Converter, Any) -> None
    """Test just structuring a primitive value."""
    val, t = primitive_and_type
    assert converter.structure(val, t) == val
    assert converter.structure(val, Any) == val


@given(seqs_of_primitives)
def test_structuring_seqs(seq_and_type):
    """Test structuring sequence generic types."""
    converter = Converter()
    iterable, t = seq_and_type
    converted = converter.structure(iterable, t)
    for x, y in zip(iterable, converted):
        assert x == y


@given(sets_of_primitives, set_types)
def test_structuring_sets(set_and_type, set_type):
    """Test structuring generic sets."""
    converter = Converter()
    set_, input_set_type = set_and_type

    if input_set_type not in (Set, FrozenSet, MutableSet):
        set_type = set_type[input_set_type.__args__[0]]

    converted = converter.structure(set_, set_type)
    assert converted == set_

    # Set[int] can't be used with isinstance any more.
    non_generic = (
        set_type.__origin__ if set_type.__origin__ is not None else set_type
    )
    assert isinstance(converted, non_generic)

    converted = converter.structure(set_, Any)
    assert converted == set_
    assert isinstance(converted, type(set_))


@given(sets_of_primitives)
def test_stringifying_sets(set_and_type):
    """Test structuring generic sets and converting the contents to str."""
    converter = Converter()
    set_, input_set_type = set_and_type

    if is_bare(input_set_type):
        input_set_type = input_set_type[str]
    else:
        input_set_type.__args__ = (str,)
    converted = converter.structure(set_, input_set_type)
    assert len(converted) == len(set_)
    for e in set_:
        assert str(e) in converted


@given(lists(primitives_and_type, min_size=1))
def test_structuring_hetero_tuples(converter, list_of_vals_and_types):
    # type: (Converter, List[Any]) -> None
    """Test structuring heterogenous tuples."""
    types = tuple(e[1] for e in list_of_vals_and_types)
    vals = [e[0] for e in list_of_vals_and_types]
    t = Tuple[types]

    converted = converter.structure(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert x == y

    for x, y in zip(types, converted):
        assert isinstance(y, x)


@given(lists(primitives_and_type))
def test_stringifying_tuples(converter, list_of_vals_and_types):
    # type: (Converter, List[Any]) -> None
    """Stringify all elements of a heterogeneous tuple."""
    vals = [e[0] for e in list_of_vals_and_types]
    t = Tuple[(str,) * len(list_of_vals_and_types)]

    converted = converter.structure(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert str(x) == y

    for x in converted:
        # this should just be unicode, but in python2, '' is not unicode
        assert isinstance(x, str)


@given(dicts_of_primitives)
def test_structuring_dicts(dict_and_type):
    converter = Converter()
    d, t = dict_and_type

    converted = converter.structure(d, t)

    assert converted == d
    assert converted is not d


@given(dicts_of_primitives, data())
def test_structuring_dicts_opts(converter, dict_and_type, data):
    # type: (Converter, Any, Any) -> None
    """Structure dicts, but with optional primitives."""
    d, t = dict_and_type
    assume(not is_bare(t))
    t.__args__ = (t.__args__[0], Optional[t.__args__[1]])
    d = {k: v if data.draw(booleans()) else None for k, v in d.items()}

    converted = converter.structure(d, t)

    assert converted == d
    assert converted is not d


@given(dicts_of_primitives)
def test_stringifying_dicts(converter, dict_and_type):
    # type: (Converter, Any) -> None
    d, t = dict_and_type

    converted = converter.structure(d, Dict[str, str])

    for k, v in d.items():
        assert converted[str(k)] == str(v)


@given(primitives_and_type)
def test_structuring_optional_primitives(converter, primitive_and_type):
    # type: (Converter, Any) -> None
    """Test structuring Optional primitive types."""
    val, type = primitive_and_type

    assert converter.structure(val, Optional[type]) == val
    assert converter.structure(None, Optional[type]) is None


@given(lists_of_primitives().filter(lambda lp: not is_bare(lp[1])))
def test_structuring_lists_of_opt(converter, list_and_type):
    # type: (Converter, List[Any]) -> None
    """Test structuring lists of Optional primitive types."""
    l, t = list_and_type

    l.append(None)
    args = t.__args__

    is_optional = args[0] is Optional or (
        is_union_type(args[0])
        and len(args[0].__args__) == 2
        and args[0].__args__[1] is NoneType
    )

    if not is_bare(t) and (args[0] not in (Any, str) and not is_optional):
        with raises((TypeError, ValueError)):
            converter.structure(l, t)

    optional_t = Optional[args[0]]
    # We want to create a generic type annotation with an optional
    # type parameter.
    t = change_type_param(t, optional_t)

    converted = converter.structure(l, t)

    for x, y in zip(l, converted):
        assert x == y

    t.__args__ = args


@given(lists_of_primitives())
def test_stringifying_lists_of_opt(converter, list_and_type):
    # type: (Converter, List[Any]) -> None
    """Test structuring Optional primitive types into strings."""
    l, t = list_and_type

    l.append(None)

    converted = converter.structure(l, List[Optional[str]])

    for x, y in zip(l, converted):
        if x is None:
            assert x is y
        else:
            assert str(x) == y


@given(lists(integers()))
def test_structuring_primitive_union_hook(converter, ints):
    # type: (Converter, List[int]) -> None
    """Registering a union loading hook works."""

    def structure_hook(val, cl):
        """Even ints are passed through, odd are stringified."""
        return val if val % 2 == 0 else str(val)

    converter.register_structure_hook(Union[str, int], structure_hook)

    converted = converter.structure(ints, List[Union[str, int]])

    for x, y in zip(ints, converted):
        if x % 2 == 0:
            assert x == y
        else:
            assert str(x) == y


def test_structure_hook_func(converter):
    """ testing the hook_func method """

    def can_handle(cls):
        return cls.__name__.startswith("F")

    def handle(obj, cls):
        return "hi"

    class Foo(object):
        pass

    class Bar(object):
        pass

    converter.register_structure_hook_func(can_handle, handle)

    assert converter.structure(10, Foo) == "hi"
    with raises(ValueError):
        converter.structure(10, Bar)


@given(data(), enums_of_primitives())
def test_structuring_enums(converter, data, enum):
    # type: (Converter, Any, Any) -> None
    """Test structuring enums by their values."""
    val = data.draw(sampled_from(list(enum)))

    assert converter.structure(val.value, enum) == val


def test_structuring_unsupported(converter):
    # type: (Converter) -> None
    """Loading unsupported classes should throw."""
    with raises(ValueError):
        converter.structure(1, Converter)
    with raises(ValueError):
        converter.structure(1, Union[int, str])


def test_subclass_registration_is_honored(converter):
    """If a subclass is registered after a superclass,
    that subclass handler should be dispatched for
    structure
    """

    class Foo(object):
        def __init__(self, value):
            self.value = value

    class Bar(Foo):
        pass

    converter.register_structure_hook(Foo, lambda obj, cls: cls("foo"))
    assert converter.structure(None, Foo).value == "foo"
    assert converter.structure(None, Bar).value == "foo"
    converter.register_structure_hook(Bar, lambda obj, cls: cls("bar"))
    assert converter.structure(None, Foo).value == "foo"
    assert converter.structure(None, Bar).value == "bar"
