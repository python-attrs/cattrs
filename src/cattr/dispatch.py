from functools import lru_cache, singledispatch
from typing import Any, Callable, List, Tuple, Union

import attr


@attr.s
class _DispatchNotFound:
    """A dummy object to help signify a dispatch not found."""

    pass


class MultiStrategyDispatch:
    """
    MultiStrategyDispatch uses a combination of exact-match dispatch,
    singledispatch, and FunctionDispatch.
    """

    __slots__ = (
        "_direct_dispatch",
        "_function_dispatch",
        "_single_dispatch",
        "_generators",
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
        except Exception:
            pass

        direct_dispatch = self._direct_dispatch.get(cl)
        if direct_dispatch is not None:
            return direct_dispatch

        return self._function_dispatch.dispatch(cl)

    def register_cls_list(self, cls_and_handler, direct: bool = False):
        """ register a class to direct or singledispatch """
        for cls, handler in cls_and_handler:
            if direct:
                self._direct_dispatch[cls] = handler
            else:
                self._single_dispatch.register(cls, handler)
                self.clear_direct()
        self.dispatch.cache_clear()

    def register_func_list(
        self,
        func_and_handler: List[
            Union[
                Tuple[Callable[[Any], bool], Any],
                Tuple[Callable[[Any], bool], Any, bool],
            ]
        ],
    ):
        """register a function to determine if the handle
        should be used for the type
        """
        for tup in func_and_handler:
            if len(tup) == 2:
                func, handler = tup
                self._function_dispatch.register(func, handler)
            else:
                func, handler, is_gen = tup
                self._function_dispatch.register(
                    func, handler, is_generator=is_gen
                )
        self.clear_direct()
        self.dispatch.cache_clear()

    def clear_direct(self):
        """Clear the direct dispatch."""
        self._direct_dispatch.clear()


class FunctionDispatch:
    """
    FunctionDispatch is similar to functools.singledispatch, but
    instead dispatches based on functions that take the type of the
    first argument in the method, and return True or False.

    objects that help determine dispatch should be instantiated objects.
    """

    __slots__ = ("_handler_pairs",)

    def __init__(self):
        self._handler_pairs = []

    def register(
        self, can_handle: Callable[[Any], bool], func, is_generator=False
    ):
        self._handler_pairs.insert(0, (can_handle, func, is_generator))

    def dispatch(self, typ):
        """
        returns the appropriate handler, for the object passed.
        """
        for can_handle, handler, is_generator in self._handler_pairs:
            # can handle could raise an exception here
            # such as issubclass being called on an instance.
            # it's easier to just ignore that case.
            try:
                ch = can_handle(typ)
            except Exception:
                continue
            if ch:
                if is_generator:
                    return handler(typ)
                else:
                    return handler
        raise KeyError("unable to find handler for {0}".format(typ))
