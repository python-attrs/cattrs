"""Test structuring of collections and primitives."""

from typing import Any, Dict, FrozenSet, List, MutableSet, Optional, Set, Tuple, Union

from attrs import define
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

from cattrs import BaseConverter
from cattrs._compat import copy_with, is_bare, is_union_type
from cattrs.errors import IterableValidationError, StructureHandlerNotFoundError

from .untyped import (
    deque_seqs_of_primitives,
    dicts_of_primitives,
    lists_of_primitives,
    primitive_strategies,
    seqs_of_primitives,
)

NoneType = type(None)
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
    lambda e: tuples(frozensets(e[0]), create_generic_type(just(FrozenSet), e[1]))
)

sets_of_primitives = one_of(mut_sets_of_primitives, frozen_sets_of_primitives)


@given(primitives_and_type)
def test_structuring_primitives(primitive_and_type):
    """Test just structuring a primitive value."""
    converter = BaseConverter()
    val, t = primitive_and_type
    assert converter.structure(val, t) == val
    assert converter.structure(val, Any) == val


@given(seqs_of_primitives)
def test_structuring_seqs(seq_and_type):
    """Test structuring sequence generic types."""
    converter = BaseConverter()
    iterable, t = seq_and_type
    converted = converter.structure(iterable, t)
    for x, y in zip(iterable, converted):
        assert x == y


@given(deque_seqs_of_primitives)
def test_structuring_seqs_to_deque(seq_and_type):
    """Test structuring sequence generic types."""
    converter = BaseConverter()
    iterable, t = seq_and_type
    converted = converter.structure(iterable, t)
    for x, y in zip(iterable, converted):
        assert x == y


@given(sets_of_primitives, set_types)
def test_structuring_sets(set_and_type, set_type):
    """Test structuring generic sets."""
    converter = BaseConverter()
    set_, input_set_type = set_and_type

    if input_set_type not in (Set, FrozenSet, MutableSet):
        set_type = set_type[input_set_type.__args__[0]]

    converted = converter.structure(set_, set_type)
    assert converted == set_

    # Set[int] can't be used with isinstance any more.
    non_generic = set_type.__origin__ if set_type.__origin__ is not None else set_type
    assert isinstance(converted, non_generic)

    converted = converter.structure(set_, Any)
    assert converted == set_
    assert isinstance(converted, type(set_))


@given(sets_of_primitives)
def test_stringifying_sets(set_and_type):
    """Test structuring generic sets and converting the contents to str."""
    converter = BaseConverter()
    set_, input_set_type = set_and_type

    if is_bare(input_set_type):
        input_set_type = input_set_type[str]
    else:
        input_set_type = copy_with(input_set_type, str)
    converted = converter.structure(set_, input_set_type)
    assert len(converted) == len(set_)
    for e in set_:
        assert str(e) in converted


@given(lists(primitives_and_type, min_size=1), booleans())
def test_structuring_hetero_tuples(list_of_vals_and_types, detailed_validation):
    """Test structuring heterogenous tuples."""
    converter = BaseConverter(detailed_validation=detailed_validation)
    types = tuple(e[1] for e in list_of_vals_and_types)
    vals = [e[0] for e in list_of_vals_and_types]
    t = Tuple[types] if types else Tuple

    converted = converter.structure(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert x == y

    for x, y in zip(types, converted):
        assert isinstance(y, x)

    t2 = Tuple[(*types, str)]  # one longer
    vals2 = [*vals, None]  # one longer
    expected_exception = IterableValidationError if detailed_validation else ValueError
    with raises(expected_exception):
        converter.structure(vals, t2)
    with raises(expected_exception):
        converter.structure(vals2, t)


@given(lists(primitives_and_type))
def test_stringifying_tuples(list_of_vals_and_types):
    """Stringify all elements of a heterogeneous tuple."""
    converter = BaseConverter()
    vals = [e[0] for e in list_of_vals_and_types]
    if len(list_of_vals_and_types):
        t = Tuple[(str,) * len(list_of_vals_and_types)]
    else:
        t = Tuple

    converted = converter.structure(vals, t)

    assert isinstance(converted, tuple)

    for x, y in zip(vals, converted):
        assert str(x) == y

    for x in converted:
        # this should just be unicode, but in python2, '' is not unicode
        assert isinstance(x, str)


@given(dicts_of_primitives)
def test_structuring_dicts(dict_and_type):
    converter = BaseConverter()
    d, t = dict_and_type

    converted = converter.structure(d, t)

    assert converted == d
    assert converted is not d


@given(dicts_of_primitives, data())
def test_structuring_dicts_opts(dict_and_type, data):
    """Structure dicts, but with optional primitives."""
    converter = BaseConverter()
    d, t = dict_and_type
    assume(not is_bare(t))
    t = copy_with(t, (t.__args__[0], Optional[t.__args__[1]]))
    d = {k: v if data.draw(booleans()) else None for k, v in d.items()}

    converted = converter.structure(d, t)

    assert converted == d
    assert converted is not d


@given(dicts_of_primitives)
def test_stringifying_dicts(dict_and_type):
    converter = BaseConverter()
    d, t = dict_and_type

    converted = converter.structure(d, Dict[str, str])

    for k, v in d.items():
        assert converted[str(k)] == str(v)


@given(primitives_and_type)
def test_structuring_optional_primitives(primitive_and_type):
    """Test structuring Optional primitive types."""
    converter = BaseConverter()
    val, type = primitive_and_type

    assert converter.structure(val, Optional[type]) == val
    assert converter.structure(None, Optional[type]) is None


@given(lists_of_primitives().filter(lambda lp: not is_bare(lp[1])), booleans())
def test_structuring_lists_of_opt(list_and_type, detailed_validation: bool) -> None:
    """Test structuring lists of Optional primitive types."""
    converter = BaseConverter(detailed_validation=detailed_validation)
    lst, t = list_and_type

    lst.append(None)
    args = t.__args__

    is_optional = args[0] is Optional or (
        is_union_type(args[0])
        and len(args[0].__args__) == 2
        and args[0].__args__[1] is NoneType
    )

    if not is_bare(t) and (args[0] not in (Any, str) and not is_optional):
        with raises(
            (TypeError, ValueError)
            if not detailed_validation
            else IterableValidationError
        ):
            converter.structure(lst, t)

    optional_t = Optional[args[0]]
    # We want to create a generic type annotation with an optional
    # type parameter.
    t = copy_with(t, optional_t)

    converted = converter.structure(lst, t)

    for x, y in zip(lst, converted):
        assert x == y


@given(lists_of_primitives())
def test_stringifying_lists_of_opt(list_and_type):
    """Test structuring Optional primitive types into strings."""
    converter = BaseConverter()
    lst, t = list_and_type

    lst.append(None)

    converted = converter.structure(lst, List[Optional[str]])

    for x, y in zip(lst, converted):
        if x is None:
            assert x is y
        else:
            assert str(x) == y


@given(lists(integers()))
def test_structuring_primitive_union_hook(ints):
    """Registering a union loading hook works."""
    converter = BaseConverter()

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


def test_structure_hook_func():
    """testing the hook_func method"""
    converter = BaseConverter()

    def can_handle(cls):
        return cls.__name__.startswith("F")

    def handle(obj, cls):
        return "hi"

    class Foo:
        pass

    class Bar:
        pass

    converter.register_structure_hook_func(can_handle, handle)

    assert converter.structure(10, Foo) == "hi"
    with raises(StructureHandlerNotFoundError) as exc:
        converter.structure(10, Bar)

    assert exc.value.type_ is Bar


def test_structuring_unsupported():
    """Loading unsupported classes should throw."""
    converter = BaseConverter()
    with raises(StructureHandlerNotFoundError) as exc:
        converter.structure(1, BaseConverter)

    assert exc.value.type_ is BaseConverter

    with raises(StructureHandlerNotFoundError) as exc:
        converter.structure(1, Union[int, str])

    assert exc.value.type_ is Union[int, str]


def test_subclass_registration_is_honored():
    """If a subclass is registered after a superclass,
    that subclass handler should be dispatched for
    structure
    """
    converter = BaseConverter()

    class Foo:
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


def test_structure_union_edge_case():
    converter = BaseConverter()

    @define
    class A:
        a1: Any
        a2: Optional[Any] = None

    @define
    class B:
        b1: Any
        b2: Optional[Any] = None

    assert converter.structure([{"a1": "foo"}, {"b1": "bar"}], List[Union[A, B]]) == [
        A("foo"),
        B("bar"),
    ]
