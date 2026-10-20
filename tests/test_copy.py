from collections import OrderedDict
from copy import deepcopy
from typing import Callable

from attr import define
from hypothesis import given
from hypothesis.strategies import just, one_of
from pytest import raises

from cattrs import BaseConverter, Converter, UnstructureStrategy
from cattrs.errors import ClassValidationError

from . import unstructure_strats


@define
class Simple:
    a: int


class Unhandled:
    """A type no hook is generated or registered for."""


def unstructure_fallback(_):
    return lambda v: "unstructured-by-fallback"


def structure_fallback(_):
    return lambda v, _type: "structured-by-fallback"


@given(strat=unstructure_strats, detailed_validation=..., prefer_attrib=...)
def test_deepcopy(
    converter_cls: type[BaseConverter],
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
    converter_cls: type[BaseConverter],
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
    """cattrs.Converter can be copied, and keeps its attributes."""
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
    converter_cls: type[BaseConverter],
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
    c.register_structure_hook(Simple, lambda v, _: Simple(v))

    assert c.unstructure(Simple(1)) == 1
    assert c.structure(1, Simple) == Simple(1)

    copy = c.copy()

    assert c is not copy

    assert c.unstructure(Simple(1)) == copy.unstructure(Simple(1))
    assert copy.structure(copy.unstructure(Simple(1)), Simple) == Simple(1)
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
    assert c._dict_factory == copy._dict_factory


@given(
    strat=unstructure_strats,
    detailed_validation=...,
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
)
def test_copy_func_hooks(
    converter_cls: type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
    dict_factory: Callable,
):
    """Un/structure function hooks are copied over."""
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
    )

    c.register_unstructure_hook_func(lambda t: t is Simple, lambda s: s.a)
    c.register_structure_hook_func(lambda t: t is Simple, lambda v, _: Simple(v))

    assert c.unstructure(Simple(1)) == 1
    assert c.structure(1, Simple) == Simple(1)

    copy = c.copy()

    assert c is not copy

    assert copy.unstructure(Simple(1)) == 1
    assert copy.structure(copy.unstructure(Simple(1)), Simple) == Simple(1)
    assert c.detailed_validation == copy.detailed_validation
    assert c._prefer_attrib_converters == copy._prefer_attrib_converters
    assert c._dict_factory == copy._dict_factory


@given(
    strat=unstructure_strats,
    detailed_validation=...,
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
)
def test_copy_fallback_factories(
    converter_cls: type[BaseConverter],
    strat: UnstructureStrategy,
    prefer_attrib: bool,
    detailed_validation: bool,
    dict_factory: Callable,
):
    """Fallback hook factories are copied over."""
    c = converter_cls(
        unstruct_strat=strat,
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
        unstructure_fallback_factory=unstructure_fallback,
        structure_fallback_factory=structure_fallback,
    )

    assert c.unstructure(Unhandled()) == "unstructured-by-fallback"
    assert c.structure("x", Unhandled) == "structured-by-fallback"

    for copy in (c.copy(), deepcopy(c)):
        assert c is not copy

        assert copy.unstructure(Unhandled()) == "unstructured-by-fallback"
        assert copy.structure("x", Unhandled) == "structured-by-fallback"


@given(strat=unstructure_strats, detailed_validation=...)
def test_copy_fallback_factories_overrides(
    strat: UnstructureStrategy, detailed_validation: bool
):
    """Fallback hook factories can be overridden on the copy."""
    c = Converter(
        unstruct_strat=strat,
        detailed_validation=detailed_validation,
        unstructure_fallback_factory=unstructure_fallback,
        structure_fallback_factory=structure_fallback,
    )

    other = c.copy(
        unstructure_fallback_factory=lambda _: lambda v: "other-unstructure",
        structure_fallback_factory=lambda _: lambda v, _type: "other-structure",
    )

    assert other.unstructure(Unhandled()) == "other-unstructure"
    assert other.structure("x", Unhandled) == "other-structure"

    # The original is untouched.
    assert c.unstructure(Unhandled()) == "unstructured-by-fallback"
    assert c.structure("x", Unhandled) == "structured-by-fallback"


@given(prefer_attrib=..., dict_factory=one_of(just(dict), just(OrderedDict)))
def test_detailed_validation(prefer_attrib: bool, dict_factory: Callable):
    """Copies with different detailed validation work correctly."""
    c = Converter(
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=True,
        dict_factory=dict_factory,
    )

    # So the converter gets generated.
    c.structure({"a": 1}, Simple)

    copy = c.copy(detailed_validation=False)

    assert c is not copy
    assert copy.detailed_validation is False

    with raises(ClassValidationError):
        c.structure({}, Simple)

    with raises(KeyError):
        copy.structure({}, Simple)


@given(
    prefer_attrib=...,
    dict_factory=one_of(just(dict), just(OrderedDict)),
    detailed_validation=...,
)
def test_col_overrides(
    prefer_attrib: bool, dict_factory: Callable, detailed_validation: bool
):
    """Copies with different sequence overrides work correctly."""
    c = Converter(
        prefer_attrib_converters=prefer_attrib,
        detailed_validation=detailed_validation,
        dict_factory=dict_factory,
        unstruct_collection_overrides={list: tuple},
    )

    # So the converter gets generated.
    assert c.unstructure([1, 2, 3]) == (1, 2, 3)
    # We also stick a manual hook on there so it gets copied too.
    c.register_unstructure_hook(Simple, lambda s: s.a)

    copy = c.copy(unstruct_collection_overrides={})

    assert c is not copy

    assert c.unstructure([1, 2, 3]) == (1, 2, 3)
    assert copy.unstructure([1, 2, 3]) == [1, 2, 3]

    assert c.unstructure(Simple(1)) == 1
    assert copy.unstructure(Simple(1)) == 1
