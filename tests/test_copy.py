from collections import OrderedDict
from copy import deepcopy
from re import S
from typing import Callable, Type

from attr import define
from hypothesis import given
from hypothesis.strategies import just, one_of

from cattrs import BaseConverter, Converter, UnstructureStrategy

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


@given(
    strat=unstructure_strats,
    detailed_validation=...,
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
)
def test_copy(
    converter_cls: Type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
    dict_factory: Callable,
):
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
    )

    copy = c.copy()

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
    assert c._dict_factory == copy._dict_factory


@given(
    strat=unstructure_strats,
    detailed_validation=...,
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
    omit_if_default=...,
)
def test_copy_converter(
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
    dict_factory: Callable,
    omit_if_default: bool,
):
    c = Converter(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
        omit_if_default=omit_if_default,
    )

    copy = c.copy()

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
    assert c._dict_factory == copy._dict_factory
    assert c.omit_if_default == copy.omit_if_default

    another_copy = c.copy(omit_if_default=not omit_if_default)
    assert c.omit_if_default != another_copy.omit_if_default


@given(
    strat=unstructure_strats,
    detailed_validation=...,
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
)
def test_copy_hooks(
    converter_cls: Type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
    dict_factory: Callable,
):
    """Un/structure hooks are copied over."""
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
    )

    c.register_unstructure_hook(Simple, lambda s: s.a)
    c.register_structure_hook(Simple, lambda v, t: Simple(v))

    assert c.unstructure(Simple(1)) == 1
    assert c.structure(1, Simple) == Simple(1)

    copy = c.copy()

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert copy.structure(copy.unstructure(Simple(1)), Simple) == Simple(1)
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
    assert c._dict_factory == copy._dict_factory
