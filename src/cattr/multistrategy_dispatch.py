from functools import lru_cache, singledispatch

import attr

from .function_dispatch import FunctionDispatch


@attr.s
class _DispatchNotFound(object):
    """ a dummy object to help signify a dispatch not found """

    pass


class MultiStrategyDispatch(object):
    """
    MultiStrategyDispatch uses a
    combination of exact-match dispatch, singledispatch, and FunctionDispatch.

    Exact match dispatch is attempted first, based on a direct
    lookup of the exact class type, if the hook was registered to avoid singledispatch.
    singledispatch is attempted next - it will handle subclasses of base classes using MRO
    If nothing is registered for singledispatch, or an exception occurs,
    the FunctionDispatch instance is then used.
    """

    __slots__ = (
        "_direct_dispatch",
        "_function_dispatch",
        "_single_dispatch",
        "dispatch",
    )

    def __init__(self, fallback_func):
        self._direct_dispatch = {}
        self._function_dispatch = FunctionDispatch()
        self._function_dispatch.register(lambda _: True, fallback_func)
        self._single_dispatch = singledispatch(_DispatchNotFound)
        self.dispatch = lru_cache(maxsize=None)(self._dispatch)

    def _dispatch(self, cl):
        try:
            dispatch = self._single_dispatch.dispatch(cl)
            if dispatch is not _DispatchNotFound:
                return dispatch

            direct_dispatch = self._direct_dispatch.get(cl)
            if direct_dispatch is not None:
                return direct_dispatch

        except Exception:
            pass
        return self._function_dispatch.dispatch(cl)

    def register_cls_list(
        self, cls_and_handler, no_singledispatch: bool = False
    ):
        """ register a class to direct or singledispatch """
        for cls, handler in cls_and_handler:
            if no_singledispatch:
                self._direct_dispatch[cls] = handler
            else:
                self._single_dispatch.register(cls, handler)
        self.dispatch.cache_clear()

    def register_func_list(self, func_and_handler):
        """register a function to determine if the handle
        should be used for the type
        """
        for func, handler in func_and_handler:
            self._function_dispatch.register(func, handler)
        self.dispatch.cache_clear()
