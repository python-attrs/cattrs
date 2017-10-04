import attr
from .function_dispatch import FunctionDispatch
from ._compat import singledispatch


@attr.s
class _DispatchNotFound(object):
    """ a dummy object to help signify a dispatch not found """
    pass


class MultiStrategyDispatch(object):
    """
    MultiStrategyDispatch uses a
    combination of FunctionDispatch and singledispatch.

    singledispatch is attempted first. If nothing is
    registered for singledispatch, or an exception occurs,
    the FunctionDispatch instance is then used.
    """

    def __init__(self, fallback_func):
        self._function_dispatch = FunctionDispatch()
        self._function_dispatch.register(lambda cls: True, fallback_func)
        self._single_dispatch = singledispatch(_DispatchNotFound)
        self._cache = {}

    def dispatch(self, cl):
        if cl not in self._cache:
            found = False
            try:
                dispatch = self._single_dispatch.dispatch(cl)
                if dispatch is not _DispatchNotFound:
                    found = True
            except Exception:
                pass
            if not found:
                dispatch = self._function_dispatch.dispatch(cl)
            self._cache[cl] = dispatch
        return self._cache[cl]

    def register_cls_list(self, cls_and_handler):
        """ register a class to singledispatch """
        for cls, handler in cls_and_handler:
            self._single_dispatch.register(cls, handler)
            if cls in self._cache:
                del self._cache[cls]

    def register_func_list(self, func_and_handler):
        """ register a function to determine if the handle
            should be used for the type
        """
        for func, handler in func_and_handler:
            self._function_dispatch.register(func, handler)
        self._cache.clear()
