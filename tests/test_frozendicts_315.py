"""Support for the built-in immutable mapping on Python 3.15+."""

from builtins import frozendict
from collections.abc import Mapping, MutableMapping
from typing import Any

import pytest
from attrs import define
from hypothesis import given
from hypothesis.strategies import booleans, dictionaries, integers, text

from cattrs import BaseConverter, Converter
from cattrs.errors import IterableValidationError


@pytest.mark.parametrize(
    "target", [frozendict, frozendict[Any, Any], frozendict[str, int]]
)
@given(values=dictionaries(text(), integers()), detailed_validation=booleans())
def test_frozendict_roundtrip(converter_cls, target, values, detailed_validation):
    """Bare and generic frozendicts roundtrip properly."""
    converter = converter_cls(detailed_validation=detailed_validation)
    result = converter.structure(values, target)
    assert type(result) is frozendict
    assert result == values
    assert converter.unstructure(result) == values


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (frozendict[int, int], {1: 2}),
        (frozendict[Any, int], {"1": 2}),
        (frozendict[int, Any], {1: "2"}),
    ],
)
def test_frozendict_conversions(converter, target, expected):
    """Frozendict keys and values are structured according to their types."""
    result = converter.structure({"1": "2"}, target)
    assert type(result) is frozendict
    assert result == expected


def test_frozendict_nested(converter):
    """Attrs classes inside frozendicts are structured and unstructured properly."""

    @define
    class Value:
        n: int

    target = frozendict[str, Value]
    result = converter.structure({"a": {"n": "1"}}, target)
    assert result == frozendict(a=Value(1))
    unstructured = converter.unstructure(result, unstructure_as=target)
    assert unstructured == {"a": {"n": 1}}
    assert type(unstructured) is (
        frozendict if type(converter) is BaseConverter else dict
    )


def test_frozendict_validation(converter):
    """Frozendict validation respects the detailed validation setting."""
    target = frozendict[int, int]
    if converter.detailed_validation:
        with pytest.raises(IterableValidationError) as exc:
            converter.structure({"1": "bad", "bad": "2"}, target)
        assert exc.value.cl in (target, frozendict)
        assert len(exc.value.exceptions) == 2
    else:
        with pytest.raises(ValueError):
            converter.structure({"1": "bad"}, target)


@pytest.mark.parametrize("target", [frozendict, frozendict[str, int]])
def test_frozendict_unstructure_overrides(target):
    """Mapping overrides apply to frozendicts unless explicitly overridden."""
    value = frozendict(a=1)
    converter = Converter(unstruct_collection_overrides={Mapping: list})
    assert converter.unstructure(value, unstructure_as=target) == [("a", 1)]

    converter = Converter(
        unstruct_collection_overrides={Mapping: list, frozendict: dict}
    )
    assert converter.unstructure(value, unstructure_as=target) == {"a": 1}

    converter = Converter(unstruct_collection_overrides={MutableMapping: list})
    assert converter.unstructure(value, unstructure_as=target) == {"a": 1}


@pytest.mark.parametrize("target", [frozendict, frozendict[str, int]])
def test_frozendict_msgspec(target):
    """Bare and nested frozendicts roundtrip through the msgspec converter."""
    make_converter = pytest.importorskip("cattrs.preconf.msgspec").make_converter

    @define
    class Container:
        value: target

    converter = make_converter()
    value = frozendict(a=1)
    assert converter.loads(converter.dumps(value, target), target) == value
    instance = Container(value)
    assert converter.loads(converter.dumps(instance), Container) == instance
