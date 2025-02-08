"""Tests for msgspec functionality."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    NamedTuple,
    Sequence,
)

from attrs import define
from hypothesis import given
from msgspec import Struct, to_builtins
from pytest import fixture

from cattrs.fns import identity
from cattrs.preconf.json import make_converter as make_json_converter
from cattrs.preconf.msgspec import MsgspecJsonConverter as Conv
from cattrs.preconf.msgspec import make_converter

from ..typed import simple_typed_classes


@define
class A:
    a: int


@define
class B:
    """This class should not be passed through to msgspec."""

    a: Any


@define
class C:
    """This class should not be passed through due to a private attribute."""

    _a: int


@dataclass
class DataclassA:
    a: int


@dataclass
class DataclassC:
    """Msgspec doesn't skip private attributes on dataclasses, so this should work OOB."""

    _a: int


class N(NamedTuple):
    a: int


class NA(NamedTuple):
    """A complex namedtuple."""

    a: A


class NC(NamedTuple):
    """A complex namedtuple."""

    a: C


class E(Enum):
    TEST = "test"


@fixture
def converter() -> Conv:
    return make_converter()


def is_passthrough(fn: Callable) -> bool:
    return fn in (identity, to_builtins)


def test_unstructure_passthrough(converter: Conv):
    """Passthrough for simple types works."""
    assert converter.get_unstructure_hook(int) == identity
    assert converter.get_unstructure_hook(float) == identity
    assert converter.get_unstructure_hook(str) == identity
    assert is_passthrough(converter.get_unstructure_hook(bytes))
    assert converter.get_unstructure_hook(None) == identity
    assert is_passthrough(converter.get_unstructure_hook(Literal[1]))
    assert is_passthrough(converter.get_unstructure_hook(E))

    # Any is special-cased, and we cannot know if it'll match
    # the msgspec behavior.
    assert not is_passthrough(converter.get_unstructure_hook(List))
    assert not is_passthrough(converter.get_unstructure_hook(Sequence))
    assert not is_passthrough(converter.get_unstructure_hook(MutableSequence))
    assert not is_passthrough(converter.get_unstructure_hook(List[Any]))
    assert not is_passthrough(converter.get_unstructure_hook(Sequence))
    assert not is_passthrough(converter.get_unstructure_hook(MutableSequence))

    assert is_passthrough(converter.get_unstructure_hook(List[int]))
    assert is_passthrough(converter.get_unstructure_hook(Sequence[int]))
    assert is_passthrough(converter.get_unstructure_hook(MutableSequence[int]))


def test_unstructure_pt_product_types(converter: Conv):
    """Passthrough for product types (attrs, dataclasses...) works."""
    assert is_passthrough(converter.get_unstructure_hook(A))
    assert not is_passthrough(converter.get_unstructure_hook(B))
    assert not is_passthrough(converter.get_unstructure_hook(C))

    assert is_passthrough(converter.get_unstructure_hook(DataclassA))
    assert is_passthrough(converter.get_unstructure_hook(DataclassC))

    assert converter.unstructure(DataclassC(1)) == {"_a": 1}

    assert is_passthrough(converter.get_unstructure_hook(N))
    assert is_passthrough(converter.get_unstructure_hook(NA))
    assert not is_passthrough(converter.get_unstructure_hook(NC))


def test_unstructure_pt_mappings(converter: Conv):
    """Mapping are passed through for unstructuring."""
    assert is_passthrough(converter.get_unstructure_hook(Dict[str, str]))
    assert is_passthrough(converter.get_unstructure_hook(Dict[int, int]))

    assert not is_passthrough(converter.get_unstructure_hook(Dict))
    assert not is_passthrough(converter.get_unstructure_hook(dict))
    assert not is_passthrough(converter.get_unstructure_hook(Dict[int, B]))
    assert not is_passthrough(converter.get_unstructure_hook(Mapping))
    assert not is_passthrough(converter.get_unstructure_hook(MutableMapping))

    assert is_passthrough(converter.get_unstructure_hook(Dict[int, A]))
    assert is_passthrough(converter.get_unstructure_hook(Mapping[int, int]))
    assert is_passthrough(converter.get_unstructure_hook(MutableMapping[int, int]))


def test_dump_hook(converter: Conv):
    """Passthrough for dump hooks works."""
    assert converter.get_dumps_hook(A) == converter.encoder.encode
    assert converter.get_dumps_hook(Dict[str, str]) == converter.encoder.encode

    # msgspec cannot handle these, so cattrs does.
    assert converter.get_dumps_hook(B) == converter.dumps


def test_get_loads_hook(converter: Conv):
    """`Converter.get_loads_hook` works."""
    hook = converter.get_loads_hook(A)
    assert hook(b'{"a": 1}') == A(1)


def test_basic_structs(converter: Conv):
    """Handling msgspec structs works."""

    class B(Struct):
        b: int

    assert converter.unstructure(B(1)) == {"b": 1}

    assert converter.structure({"b": 1}, B) == B(1)


@given(simple_typed_classes(text_codec="ascii", allow_infinity=False, allow_nan=False))
def test_simple_classes(cls_and_vals):
    cl, posargs, kwargs = cls_and_vals

    msgspec = make_converter()
    json = make_json_converter()

    inst = cl(*posargs, **kwargs)

    rebuilt_msgspec = msgspec.loads(msgspec.dumps(inst), cl)
    rebuilt_json = json.loads(json.dumps(inst), cl)

    assert rebuilt_msgspec == rebuilt_json
