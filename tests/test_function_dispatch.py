from cattrs import BaseConverter
from cattrs.dispatch import FunctionDispatch


def test_function_dispatch():
    dispatch = FunctionDispatch(BaseConverter())

    assert dispatch.dispatch(float) is None

    test_func = object()

    dispatch.register(lambda cls: issubclass(cls, float), test_func)

    assert dispatch.dispatch(float) == test_func


def test_function_clears_cache_after_function_added():
    dispatch = FunctionDispatch(BaseConverter())

    class Foo:
        pass

    Foo()

    class Bar(Foo):
        pass

    Bar()

    dispatch.register(lambda cls: issubclass(cls, Foo), "foo")
    assert dispatch.dispatch(Bar) == "foo"
    dispatch.register(lambda cls: issubclass(cls, Bar), "bar")
    assert dispatch.dispatch(Bar) == "bar"
