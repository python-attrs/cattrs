"""Tests for dumping."""
from . import (seqs_of_primitives, dicts_of_primitives, enums_of_primitives,
               simple_classes, nested_classes)

from cattr.converters import UnstructureStrategy

from attr import asdict, astuple
from hypothesis import given
from hypothesis.strategies import sampled_from, choices

unstruct_strats = sampled_from([
    UnstructureStrategy.AS_DICT, UnstructureStrategy.AS_TUPLE])

# Primitive stuff first.


@given(seqs_of_primitives, unstruct_strats)
def test_seq_unstructure(converter, seq_and_type, dump_strat):
    # type: (Converter, Any, UnstructureStrategy) -> None
    """Dumping a sequence of primitives is a simple copy operation."""
    converter.unstruct_strat = dump_strat
    assert converter.unstruct_strat is dump_strat
    seq = seq_and_type[0]
    dumped = converter.unstructure(seq)
    assert dumped == seq
    if not isinstance(seq, tuple):
        assert dumped is not seq
    assert type(dumped) is type(seq)


@given(dicts_of_primitives, unstruct_strats)
def test_mapping_unstructure(converter, map_and_type, dump_strat):
    # type: (Converter, Any, UnstructureStrategy) -> None
    """Dumping a mapping of primitives is a simple copy operation."""
    converter.unstruct_strat = dump_strat
    mapping = map_and_type[0]
    dumped = converter.unstructure(mapping)
    assert dumped == mapping
    assert dumped is not mapping
    assert type(dumped) is type(mapping)


@given(enums_of_primitives(), unstruct_strats, choices())
def test_enum_unstructure(converter, enum, dump_strat,
                          choice):
    # type: (Converter, EnumMeta, UnstructureStrategy) -> None
    """Dumping enums of primitives converts them to their primitives."""
    converter.unstruct_strat = dump_strat

    member = choice(list(enum.__members__.values()))

    assert converter.unstructure(member) == member.value


@given(nested_classes)
def test_attrs_asdict_unstructure(converter, nested_class):
    # type: (Converter, Type) -> None
    """Our dumping should be identical to `attrs`."""
    instance = nested_class[0]()
    assert converter.unstructure(instance) == asdict(instance)


@given(nested_classes)
def test_attrs_astuple_unstructure(converter, nested_class):
    # type: (Converter, Type) -> None
    """Our dumping should be identical to `attrs`."""
    converter.unstruct_strat = UnstructureStrategy.AS_TUPLE
    instance = nested_class[0]()
    assert converter.unstructure(instance) == astuple(instance)


@given(simple_classes())
def test_unstructure_hooks(converter, cl_and_vals):
    """
    Unstructure hooks work.
    """
    cl, vals = cl_and_vals
    inst = cl(*vals)

    converter.register_unstructure_hook(cl, lambda val: 'test')

    assert converter.unstructure(inst) == 'test'


def test_unstructure_hook_func(converter):
    """
    Unstructure hooks work.
    """
    def can_handle(cls):
        return cls.__name__.startswith("F")

    def handle(obj):
        return "hi"

    class Foo(object):
        pass

    class Bar(object):
        pass

    converter.register_unstructure_hook_func(can_handle, handle)

    b = Bar()
    assert converter.unstructure(Foo()) == "hi"
    assert converter.unstructure(b) is b
