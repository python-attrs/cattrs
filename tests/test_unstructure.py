"""Tests for dumping."""
from enum import EnumMeta

from . import (seqs_of_primitives, dicts_of_primitives, enums_of_primitives,
               nested_classes)

from cattr._compat import Any, Type
from cattr.converters import Converter, UnstructureStrategy

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
    seq = seq_and_type[0]
    dumped = converter.unstructure(seq)
    assert dumped == seq
    assert dumped is not seq
    assert type(dumped) is type(seq)


@given(dicts_of_primitives, unstruct_strats)
def test_mapping_unstructure(converter, map_and_type, dump_strat):
    # type: (Converter, Any, UnstructureStrategy) -> None
    """Dumping a mapping of primitives is a simple copy operation."""
    converter.dumping_strat = dump_strat
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
    converter.dumping_strat = dump_strat

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
