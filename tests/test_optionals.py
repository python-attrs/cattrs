from typing import NewType

from attrs import define


def test_newtype_optionals(genconverter):
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
