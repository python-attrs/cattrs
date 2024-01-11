"""Tests for msgspec functionality."""
from typing import Callable, List

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

    # Any is special-cased, and we cannot know if it'll match
    # the msgspec behavior.
    assert not is_passthrough(converter.get_unstructure_hook(List))

    assert is_passthrough(converter.get_unstructure_hook(List[int]))


def test_unstructure_pt_attrs(converter: Conv):
    """Passthrough for attrs works."""
    assert is_passthrough(converter.get_unstructure_hook(A))


def test_dump_hook_attrs(converter: Conv):
    """Passthrough for dump hooks works."""
    assert converter.get_dumps_hook(A) == converter.encoder.encode


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
