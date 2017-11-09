import attr


@attr.s(slots=True)
class FunctionDispatch(object):
    """
    FunctionDispatch is similar to functools.singledispatch, but
    instead dispatches based on functions that take the type of the
    first argument in the method, and return True or False.

    objects that help determine dispatch should be instantiated objects.
    """
    _handler_pairs = attr.ib(init=False, default=attr.Factory(list))
    _cache = attr.ib(init=False, default=attr.Factory(dict))

    def register(self, can_handle, func):
        self._handler_pairs.insert(0, (can_handle, func))
        self._cache.clear()

    def dispatch(self, typ):
        """
        returns the appropriate handler, for the object passed.
        """
        try:
            return self._cache[typ]
        except KeyError:
            self._cache[typ] = self._dispatch(typ)
            return self._cache[typ]

    def _dispatch(self, typ):
        for can_handle, handler in self._handler_pairs:
            # can handle could raise an exception here
            # such as issubclass being called on an instance.
            # it's easier to just ignore that case.
            try:
                if can_handle(typ):
                    return handler
            except Exception:
                pass
        raise KeyError("unable to find handler for {0}".format(typ))
