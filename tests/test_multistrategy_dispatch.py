from cattrs.dispatch import MultiStrategyDispatch


class Foo(object):
    pass


def _fallback():
    pass


def _foo_func():
    pass


def _foo_cls():
    pass


def test_multistrategy_dispatch_register_cls():
    _fallback()
    _foo_func()
    _foo_cls()
    dispatch = MultiStrategyDispatch(_fallback)
    assert dispatch.dispatch(Foo) == _fallback
    dispatch.register_cls_list([(Foo, _foo_cls)])
    assert dispatch.dispatch(Foo) == _foo_cls


def test_multistrategy_dispatch_register_func():
    dispatch = MultiStrategyDispatch(_fallback)
    assert dispatch.dispatch(Foo) == _fallback
    dispatch.register_func_list([(lambda cls: issubclass(cls, Foo), _foo_func)])
    assert dispatch.dispatch(Foo) == _foo_func


def test_multistrategy_dispatch_conflict_class_wins():
    """
    When a class dispatch and a function dispatch
    are registered which handle the same type, the
    class dispatch should return.
    """
    dispatch = MultiStrategyDispatch(_fallback)
    dispatch.register_func_list([(lambda cls: issubclass(cls, Foo), _foo_func)])
    dispatch.register_cls_list([(Foo, _foo_cls)])
    assert dispatch.dispatch(Foo) == _foo_cls
