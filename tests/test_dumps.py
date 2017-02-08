"""Tests for dumping."""
from enum import EnumMeta

from . import (seqs_of_primitives, dicts_of_primitives, enums_of_primitives,
               nested_classes)

from cattr.converters import Converter, AttrsDumpingStrategy

from attr import asdict, astuple
from hypothesis import given
from hypothesis.strategies import sampled_from, choices

dump_strats = sampled_from(["asdict", "astuple"])

# Primitive stuff first.


@given(seqs_of_primitives, dump_strats)
def test_seq_dumping(converter: Converter, seq_and_type, dump_strat):
    """Dumping a sequence of primitives is a simple copy operation."""
    converter.dumping_strat = dump_strat
    seq = seq_and_type[0]
    dumped = converter.dumps(seq)
    assert dumped == seq
    assert dumped is not seq
    assert type(dumped) is type(seq)


@given(dicts_of_primitives, dump_strats)
def test_mapping_dumping(converter, map_and_type, dump_strat):
    """Dumping a mapping of primitives is a simple copy operation."""
    converter.dumping_strat = dump_strat
    mapping = map_and_type[0]
    dumped = converter.dumps(mapping)
    assert dumped == mapping
    assert dumped is not mapping
    assert type(dumped) is type(mapping)


@given(enums_of_primitives(), dump_strats, choices())
def test_enum_dumping(converter: Converter, enum: EnumMeta, dump_strat,
                      choice):
    """Dumping enums of primitives converts them to their primitives."""
    converter.dumping_strat = dump_strat

    member = choice(list(enum.__members__.values()))

    assert converter.dumps(member) == member.value


@given(nested_classes)
def test_attrs_asdict_dumping(converter: Converter, nested_class):
    """Our dumping should be identical to `attrs`."""
    instance = nested_class()
    assert converter.dumps(instance) == asdict(instance)


@given(nested_classes)
def test_attrs_astuple_dumping(converter: Converter, nested_class):
    """Our dumping should be identical to `attrs`."""
    converter.dumping_strat = "astuple"
    assert converter.dumping_strat is AttrsDumpingStrategy.AS_TUPLE
    instance = nested_class()
    assert converter.dumps(instance) == astuple(instance)
