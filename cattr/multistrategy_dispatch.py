from .function_dispatch import FunctionDispatch
from ._compat import singledispatch


class MultiStrategyDispatch(object):
    """
    MultiStrategyDispatch uses a
    combination of function dispatch and singledispatch.

    FunctionDispatches are used first, then uses singledispatch otherwise.
    """

    def __init__(self, fallback_func):
        self._function_dispatch = FunctionDispatch()
        self._function_dispatch.register(lambda cls: True, fallback_func)
        self._single_dispatch = singledispatch(lambda: None)
        del self._single_dispatch.registry[object]
        self._cache = {}

    def dispatch(self, cl):
        if cl not in self._cache:
            found = False
            try:
                dispatch = self._single_dispatch.dispatch(cl)
                if dispatch is not None:
                    found = True
            except Exception:
                pass
            if not found:
                dispatch = self._function_dispatch.dispatch(cl)
            self._cache[cl] = dispatch
        return self._cache[cl]

    def register_cls(self, cls, handler):
        """ register a class, which utilizes singledispatch """
        self._single_dispatch.register(cls, handler)

    def register_func(self, func, handler):
        """ register a function to determine if the handle should be used for the type """
        self._function_dispatch.register(func, handler)
