from typing import Any, NewType, Optional

import pytest
from attrs import define

from cattrs import BaseConverter, Converter

from ._compat import is_py310_plus


def test_newtype_optionals(genconverter):
    """Newtype optionals should work."""
    Foo = NewType("Foo", str)

    genconverter.register_unstructure_hook(Foo, lambda v: v.replace("foo", "bar"))

    @define
    class ModelWithFoo:
        total_foo: Foo
        maybe_foo: Optional[Foo]

    assert genconverter.unstructure(ModelWithFoo(Foo("foo"), Foo("is it a foo?"))) == {
        "total_foo": "bar",
        "maybe_foo": "is it a bar?",
    }


@pytest.mark.skipif(not is_py310_plus, reason="3.10+ union syntax")
def test_newtype_modern_optionals(genconverter):
    """Newtype optionals should work."""
    Foo = NewType("Foo", str)

    genconverter.register_unstructure_hook(Foo, lambda v: v.replace("foo", "bar"))

    @define
    class ModelWithFoo:
        total_foo: Foo
        maybe_foo: Foo | None

    assert genconverter.unstructure(ModelWithFoo(Foo("foo"), Foo("is it a foo?"))) == {
        "total_foo": "bar",
        "maybe_foo": "is it a bar?",
    }


def test_optional_any(converter: Converter):
    """Unstructuring Any|None is equivalent to unstructuring as v.__class__."""

    @define
    class A:
        pass

    assert converter.unstructure(A(), Optional[Any]) == {}


def test_override_optional(converter: BaseConverter):
    """Optionals can be overridden using singledispatch."""

    @converter.register_structure_hook
    def _(val, _) -> Optional[int]:
        if val in ("", None):
            return None
        return int(val)

    assert converter.structure("", Optional[int]) is None
    assert converter.structure("1", Optional[int]) == 1

    @converter.register_unstructure_hook
    def _(val: Optional[int]) -> Any:
        if val in (None, 0):
            return None
        return val

    assert converter.unstructure(0, Optional[int]) is None
    assert converter.unstructure(5, Optional[int]) == 5
