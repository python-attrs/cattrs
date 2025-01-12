"""Tests for dumping."""

from attrs import asdict, astuple
from hypothesis import given
from hypothesis.strategies import data, just, lists, one_of, sampled_from

from cattrs.converters import BaseConverter, UnstructureStrategy

from .untyped import (
    dicts_of_primitives,
    enums_of_primitives,
    nested_classes,
    seqs_of_primitives,
    sets_of_primitives,
    simple_classes,
)

unstruct_strats = sampled_from(
    [UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE]
)

# Primitive stuff first.


@given(seqs_of_primitives, unstruct_strats)
def test_seq_unstructure(seq_and_type, dump_strat):
    """Dumping a sequence of primitives is a simple copy operation."""
    converter = BaseConverter(unstruct_strat=dump_strat)
    assert converter.unstruct_strat is dump_strat
    seq = seq_and_type[0]
    dumped = converter.unstructure(seq)
    assert dumped == seq
    if not isinstance(seq, tuple):
        assert dumped is not seq
    assert type(dumped) is type(seq)


@given(sets_of_primitives, unstruct_strats)
def test_set_unstructure(set_and_type, dump_strat):
    """Dumping a set of primitives is a simple copy operation."""
    converter = BaseConverter(unstruct_strat=dump_strat)
    assert converter.unstruct_strat is dump_strat
    set = set_and_type[0]
    dumped = converter.unstructure(set)
    assert dumped == set
    if set:
        assert dumped is not set
    assert type(dumped) is type(set)


@given(dicts_of_primitives, unstruct_strats)
def test_mapping_unstructure(map_and_type, dump_strat):
    """Dumping a mapping of primitives is a simple copy operation."""
    converter = BaseConverter(unstruct_strat=dump_strat)
    mapping = map_and_type[0]
    dumped = converter.unstructure(mapping)
    assert dumped == mapping
    assert dumped is not mapping
    assert type(dumped) is type(mapping)


@given(enums_of_primitives(), unstruct_strats, data())
def test_enum_unstructure(enum, dump_strat, data):
    """Dumping enums of primitives converts them to their primitives."""
    converter = BaseConverter(unstruct_strat=dump_strat)

    member = data.draw(sampled_from(list(enum.__members__.values())))

    assert converter.unstructure(member) == member.value


@given(nested_classes())
def test_attrs_asdict_unstructure(nested_class):
    """Our dumping should be identical to `attrs`."""
    converter = BaseConverter()
    instance = nested_class[0]()
    assert converter.unstructure(instance) == asdict(instance)


@given(nested_classes())
def test_attrs_astuple_unstructure(nested_class):
    """Our dumping should be identical to `attrs`."""
    converter = BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
    instance = nested_class[0]()
    assert converter.unstructure(instance) == astuple(instance)


@given(simple_classes())
def test_unstructure_hooks(cl_and_vals):
    """
    Unstructure hooks work.
    """
    converter = BaseConverter()
    cl, vals, kwargs = cl_and_vals
    inst = cl(*vals, **kwargs)

    converter.register_unstructure_hook(cl, lambda _: "test")

    assert converter.unstructure(inst) == "test"


def test_unstructure_hook_func(converter):
    """
    Unstructure hooks work.
    """

    def can_handle(cls):
        return cls.__name__.startswith("F")

    def handle(_):
        return "hi"

    class Foo:
        pass

    class Bar:
        pass

    converter.register_unstructure_hook_func(can_handle, handle)

    b = Bar()
    assert converter.unstructure(Foo()) == "hi"
    assert converter.unstructure(b) is b


@given(lists(simple_classes()), one_of(just(tuple), just(list)))
def test_seq_of_simple_classes_unstructure(cls_and_vals, seq_type: type):
    """Dumping a sequence of primitives is a simple copy operation."""
    converter = BaseConverter()

    inputs = seq_type(cl(*vals, **kwargs) for cl, vals, kwargs in cls_and_vals)
    outputs = converter.unstructure(inputs)
    assert type(outputs) is seq_type
    assert all(type(e) is dict for e in outputs)
