from typing import Any

from attrs import frozen

from .constraints import ConstraintPathSentinel


@frozen(slots=False, init=False)
class _ValDummy:
    """A validation dummy, used to gather the validation hooks."""

    def __init__(self, path: tuple[str, ...]) -> None:
        # We use a dotted name in `__dict__` to avoid clashes in `getattr`
        self.__dict__[".path"] = path

    def __getattr__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))

    def __getitem__(self, name: str) -> Any:
        return _ValDummy(path=(*self.__dict__[".path"], name))

    def __iter__(self):
        yield _ValDummy(path=(*self.__dict__[".path"], ConstraintPathSentinel.EACH))
