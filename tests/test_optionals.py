from typing import NewType, Optional

import pytest
from attrs import define

from cattrs._compat import is_py310_plus


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
