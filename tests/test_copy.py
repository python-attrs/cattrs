from copy import deepcopy
from typing import Type

from attr import define
from hypothesis import given

from cattrs import BaseConverter, UnstructureStrategy

from . import unstructure_strats


@define
class Simple:
    a: int


@given(strat=unstructure_strats, detailed_validation=..., prefer_attrib=...)
def test_deepcopy(
    converter_cls: Type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
):
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
    )

    copy = deepcopy(c)

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters


@given(strat=unstructure_strats, detailed_validation=..., prefer_attrib=...)
def test_copy(
    converter_cls: Type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
):
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
    )

    copy = c.copy()

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
