import pytest

from cattrs.dispatch import FunctionDispatch
from cattrs.errors import StructureHandlerNotFoundError


def test_function_dispatch():
    dispatch = FunctionDispatch()

    with pytest.raises(StructureHandlerNotFoundError) as exc:
        dispatch.dispatch(float)

    assert exc.value.type_ is float

    test_func = object()

    dispatch.register(lambda cls: issubclass(cls, float), test_func)

    assert dispatch.dispatch(float) == test_func


def test_function_clears_cache_after_function_added():
    dispatch = FunctionDispatch()

    class Foo(object):
        pass

    Foo()

    class Bar(Foo):
        pass

    Bar()

    dispatch.register(lambda cls: issubclass(cls, Foo), "foo")
    assert dispatch.dispatch(Bar) == "foo"
    dispatch.register(lambda cls: issubclass(cls, Bar), "bar")
    assert dispatch.dispatch(Bar) == "bar"
