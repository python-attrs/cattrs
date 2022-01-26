"""Test un/structuring class graphs with ForwardRef."""
# This file is almost same as test_forwardref.py but with
# PEP 563 (delayed evaluation of annotations) enabled.
# Even though with PEP 563 the explicit ForwardRefs
# (with string quotes) would not always be needed, they
# still can be used.
from __future__ import annotations
from typing import List, Tuple, ForwardRef
from dataclasses import dataclass

import pytest

from attr import define

from cattr import Converter, GenConverter, resolve_types

from . import module


@define
class A2:
    val: "B_1"


@dataclass
class A2_DC:
    val: "B_2"


B_1 = int
B_2 = int


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_simple_ref(converter_cls):
    c = converter_cls()

    orig = A2(1)
    unstructured = c.unstructure(orig, A2)

    assert unstructured == {"val": 1}

    assert c.structure(unstructured, A2) == orig


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_simple_ref_dataclass(converter_cls):
    c = converter_cls()

    orig = A2_DC(1)
    unstructured = c.unstructure(orig, A2_DC)

    assert unstructured == {"val": 1}

    assert c.structure(unstructured, A2_DC) == orig


@define
class A3:
    val: List["B3_1"]


@dataclass
class A3_DC:
    val: List["B3_2"]


B3_1 = int
B3_2 = int


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_nested_ref(converter_cls):
    c = converter_cls()

    orig = A3([1])
    unstructured = c.unstructure(orig, A3)

    assert unstructured == {"val": [1]}

    assert c.structure(unstructured, A3) == orig


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_nested_ref_dataclass(converter_cls):
    c = converter_cls()

    orig = A3_DC([1])
    unstructured = c.unstructure(orig, A3_DC)

    assert unstructured == {"val": [1]}

    assert c.structure(unstructured, A3_DC) == orig


@define
class AClassChild(module.AClass):
    x: str


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_nested_ref_imported(converter_cls):
    c = converter_cls()

    orig = AClassChild(ival=1, ilist=[2, 3], x="4")
    unstructured = c.unstructure(orig, AClassChild)

    assert unstructured == {"ival": 1, "ilist": [2, 3], "x": "4"}

    assert c.structure(unstructured, AClassChild) == orig


@dataclass
class DClassChild(module.DClass):
    x: str


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_nested_ref_imported_dataclass(converter_cls):
    c = converter_cls()

    orig = DClassChild(ival=1, ilist=[2, 3], x="4")
    unstructured = c.unstructure(orig, DClassChild)

    assert unstructured == {"ival": 1, "ilist": [2, 3], "x": "4"}

    assert c.structure(unstructured, DClassChild) == orig


@define
class Dummy:
    a: int


RecursiveTypeAlias_1 = List[Tuple[Dummy, "RecursiveTypeAlias_1"]]
RecursiveTypeAlias_2 = List[Tuple[Dummy, "RecursiveTypeAlias_2"]]


@define
class ATest:
    test: RecursiveTypeAlias_1


@dataclass
class DTest:
    test: RecursiveTypeAlias_2


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_recursive_type_alias_manual_registration(converter_cls):
    c = converter_cls()
    c.register_structure_hook(
        ForwardRef("RecursiveTypeAlias_1"),
        lambda obj, _: c.structure(obj, RecursiveTypeAlias_1),
    )
    c.register_unstructure_hook(
        ForwardRef("RecursiveTypeAlias_1"),
        lambda obj: c.unstructure(obj, RecursiveTypeAlias_1),
    )
    c.register_structure_hook(
        ForwardRef("RecursiveTypeAlias_2"),
        lambda obj, _: c.structure(obj, RecursiveTypeAlias_2),
    )
    c.register_unstructure_hook(
        ForwardRef("RecursiveTypeAlias_2"),
        lambda obj: c.unstructure(obj, RecursiveTypeAlias_2),
    )

    orig = [(Dummy(1), [(Dummy(2), [(Dummy(3), [])])])]
    unstructured = c.unstructure(orig, RecursiveTypeAlias_1)

    assert unstructured == [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]

    assert c.structure(unstructured, RecursiveTypeAlias_1) == orig

    orig = ATest(test=[(Dummy(1), [(Dummy(2), [(Dummy(3), [])])])])
    unstructured = c.unstructure(orig, ATest)

    assert unstructured == {
        "test": [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]
    }

    assert c.structure(unstructured, ATest) == orig

    orig = DTest(test=[(Dummy(1), [(Dummy(2), [(Dummy(3), [])])])])
    unstructured = c.unstructure(orig, DTest)

    assert unstructured == {
        "test": [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]
    }

    assert c.structure(unstructured, DTest) == orig


RecursiveTypeAlias3 = List[Tuple[Dummy, "RecursiveTypeAlias3"]]

resolve_types(RecursiveTypeAlias3, globals(), locals())


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_recursive_type_alias_cattr_resolution(converter_cls):
    c = converter_cls()

    orig = [(Dummy(1), [(Dummy(2), [(Dummy(3), [])])])]
    unstructured = c.unstructure(orig, RecursiveTypeAlias3)

    assert unstructured == [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]

    assert c.structure(unstructured, RecursiveTypeAlias3) == orig


@define
class ATest4:
    test: module.RecursiveTypeAliasM_1


@dataclass
class DTest4:
    test: module.RecursiveTypeAliasM_2


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_recursive_type_alias_imported(converter_cls):
    c = converter_cls()

    orig = [
        (
            module.ModuleClass(1),
            [(module.ModuleClass(2), [(module.ModuleClass(3), [])])],
        )
    ]
    unstructured = c.unstructure(orig, module.RecursiveTypeAliasM)

    assert unstructured == [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]

    assert c.structure(unstructured, module.RecursiveTypeAliasM) == orig

    orig = ATest4(
        test=[
            (
                module.ModuleClass(1),
                [(module.ModuleClass(2), [(module.ModuleClass(3), [])])],
            )
        ]
    )
    unstructured = c.unstructure(orig, ATest4)

    assert unstructured == {
        "test": [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]
    }

    assert c.structure(unstructured, ATest4) == orig

    orig = DTest4(
        test=[
            (
                module.ModuleClass(1),
                [(module.ModuleClass(2), [(module.ModuleClass(3), [])])],
            )
        ]
    )
    unstructured = c.unstructure(orig, DTest4)

    assert unstructured == {
        "test": [({"a": 1}, [({"a": 2}, [({"a": 3}, [])])])]
    }

    assert c.structure(unstructured, DTest4) == orig
