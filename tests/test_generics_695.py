"""Tests for PEP 695 (Type Parameter Syntax)."""

from dataclasses import dataclass

import pytest
from attrs import define

from cattrs import BaseConverter, Converter

from ._compat import is_py312_plus


@pytest.mark.skipif(not is_py312_plus, reason="3.12+ syntax")
def test_simple_generic_roundtrip(converter: BaseConverter):
    """PEP 695 attrs generics work."""

    @define
    class A[T]:
        a: T

    assert converter.structure({"a": "1"}, A[int]) == A(1)
    assert converter.unstructure(A(1)) == {"a": 1}

    if isinstance(converter, Converter):
        # Only supported on a Converter
        assert converter.unstructure(A(1), A[int]) == {"a": 1}


@pytest.mark.skipif(not is_py312_plus, reason="3.12+ syntax")
def test_simple_generic_roundtrip_dc(converter: BaseConverter):
    """PEP 695 dataclass generics work."""

    @dataclass
    class A[T]:
        a: T

    assert converter.structure({"a": "1"}, A[int]) == A(1)
    assert converter.unstructure(A(1)) == {"a": 1}

    if isinstance(converter, Converter):
        # Only supported on a Converter
        assert converter.unstructure(A(1), A[int]) == {"a": 1}


def test_type_aliases(converter: BaseConverter):
    """PEP 695 type aliases work."""
    type my_int = int

    assert converter.structure("42", my_int) == 42
    assert converter.unstructure(42, my_int) == 42

    type my_other_int = int

    # Manual hooks should work.

    converter.register_structure_hook_func(
        lambda t: t is my_other_int, lambda v, _: v + 10
    )
    converter.register_unstructure_hook_func(
        lambda t: t is my_other_int, lambda v: v - 20
    )

    assert converter.structure(1, my_other_int) == 11
    assert converter.unstructure(100, my_other_int) == 80


def test_type_aliases_simple_hooks(converter: BaseConverter):
    """PEP 695 type aliases work with `register_un/structure_hook`."""
    type my_other_int = int

    converter.register_structure_hook(my_other_int, lambda v, _: v + 10)
    converter.register_unstructure_hook(my_other_int, lambda v: v - 20)

    assert converter.structure(1, my_other_int) == 11
    assert converter.unstructure(100, my_other_int) == 80


def test_type_aliases_overwrite_base_hooks(converter: BaseConverter):
    """Overwriting base hooks should affect type aliases."""
    converter.register_structure_hook(int, lambda v, _: v + 10)
    converter.register_unstructure_hook(int, lambda v: v - 20)

    type my_int = int

    assert converter.structure(1, my_int) == 11
    assert converter.unstructure(100, my_int) == 80


def test_type_alias_with_children(converter: BaseConverter):
    """A type alias that chains to a hook that requires the type parameter works."""

    class TestClass:
        pass

    def structure_testclass(val, type):
        assert type is TestClass
        return TestClass

    converter.register_structure_hook(TestClass, structure_testclass)

    type TestAlias = TestClass
    assert converter.structure(None, TestAlias) is TestClass


def test_generic_type_alias(converter: BaseConverter):
    """Generic type aliases work.

    See https://docs.python.org/3/reference/compound_stmts.html#generic-type-aliases
    for details.
    """

    type Gen1[T] = T

    assert converter.structure("1", Gen1[int]) == 1

    type Gen2[K, V] = dict[K, V]

    assert converter.structure({"a": "1"}, Gen2[str, int]) == {"a": 1}
