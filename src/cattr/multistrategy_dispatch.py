from typing import TypeVar

import attr
from .function_dispatch import FunctionDispatch
from ._compat import singledispatch, lru_cache


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

    __slots__ = ("_function_dispatch", "_single_dispatch", "dispatch")

    def __init__(self, fallback_func):
        self._function_dispatch = FunctionDispatch()
        self._function_dispatch.register(lambda cls: True, fallback_func)
        self._single_dispatch = singledispatch(_DispatchNotFound)
        self.dispatch = lru_cache(64)(self._dispatch)

    def _dispatch(self, cl, mappings: dict = None):
        if isinstance(cl, TypeVar):
            # We have a generic, lets try and check the mappings
            cl = getattr(mappings, cl.__name__, cl)

        try:
            dispatch = self._single_dispatch.dispatch(cl)
            if dispatch is not _DispatchNotFound:
                return lambda x: dispatch(x, cl, mappings)
        except Exception:
            pass
        dis = self._function_dispatch.dispatch(cl)
        return lambda x: dis(x, cl, mappings)

    def register_cls_list(self, cls_and_handler):
        """ register a class to singledispatch """
        for cls, handler in cls_and_handler:
            self._single_dispatch.register(cls, handler)
        self.dispatch.cache_clear()

    def register_func_list(self, func_and_handler):
        """ register a function to determine if the handle
            should be used for the type
        """
        for func, handler in func_and_handler:
            self._function_dispatch.register(func, handler)
        self.dispatch.cache_clear()
