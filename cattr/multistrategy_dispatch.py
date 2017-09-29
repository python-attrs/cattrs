from .function_dispatch import FunctionDispatch
from ._compat import singledispatch


class MultiStrategyDispatch(object):
    """
    MultiStrategyDispatch uses a
    combination of function dispatch and singledispatch.

    FunctionDispatches are used first, then uses singledispatch otherwise.
    """

    def __init__(self, fallback_func):
        self._dispatch_not_found = object()
        self._function_dispatch = FunctionDispatch()
        self._function_dispatch.register(lambda cls: True, fallback_func)
        self._single_dispatch = singledispatch(self._dispatch_not_found)
        self._cache = {}

    @staticmethod
    def _clear_registry(singledispatch_instance):
        """
        a hack to clear the singledispatch registry.

        this ensures that singledispatch does not resolve for
        types that are not explicitly registered to it.
        """
        register_closure = singledispatch_instance.register.__closure__
        for cell in register_closure:
            if isinstance(cell.cell_contents, dict):
                if object in cell.cell_contents:
                    del cell.cell_contents[object]

    def dispatch(self, cl):
        if cl not in self._cache:
            found = False
            try:
                dispatch = self._single_dispatch.dispatch(cl)
                if dispatch is not self._dispatch_not_found:
                    found = True
            except Exception as e:
                pass
            if not found:
                dispatch = self._function_dispatch.dispatch(cl)
            self._cache[cl] = dispatch
        return self._cache[cl]

    def register_cls(self, cls, handler):
        """ register a class, which utilizes singledispatch """
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
