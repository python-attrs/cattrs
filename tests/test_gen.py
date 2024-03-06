"""Tests for functionality from the gen module."""

import linecache
from traceback import format_exc

from attrs import define

from cattrs import Converter
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn


def test_structure_linecache():
    """Linecaching for structuring should work."""

    @define
    class A:
        a: int

    c = Converter(detailed_validation=False)
    try:
        c.structure({"a": "test"}, A)
    except ValueError:
        res = format_exc()
        assert "'a'" in res


def test_unstructure_linecache():
    """Linecaching for unstructuring should work."""

    @define
    class Inner:
        a: int

    @define
    class Outer:
        inner: Inner

    c = Converter()
    try:
        c.unstructure(Outer({}))
    except AttributeError:
        res = format_exc()
        assert "'a'" in res


def test_no_linecache():
    """Linecaching should be disableable."""

    @define
    class A:
        a: int

    c = Converter()
    before = len(linecache.cache)
    c.structure(c.unstructure(A(1)), A)
    after = len(linecache.cache)

    assert after == before + 2

    @define
    class B:
        a: int

    before = len(linecache.cache)
    c.register_structure_hook(
        B, make_dict_structure_fn(B, c, _cattrs_use_linecache=False)
    )
    c.register_unstructure_hook(
        B, make_dict_unstructure_fn(B, c, _cattrs_use_linecache=False)
    )
    c.structure(c.unstructure(B(1)), B)

    assert len(linecache.cache) == before


def test_linecache_dedup():
    """Linecaching avoids duplicates."""

    @define
    class LinecacheA:
        a: int

    c = Converter()
    before = len(linecache.cache)
    c.structure(c.unstructure(LinecacheA(1)), LinecacheA)
    after = len(linecache.cache)

    assert after == before + 2

    c = Converter()

    c.structure(c.unstructure(LinecacheA(1)), LinecacheA)

    assert len(linecache.cache) == after
