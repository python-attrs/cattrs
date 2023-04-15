"""Tests for TypedDict un/structuring."""
from datetime import datetime
from inspect import get_annotations

from hypothesis import assume, given
from hypothesis.strategies import booleans

from cattrs import Converter
from cattrs._compat import is_generic
from cattrs.gen._generics import generate_mapping

from .typeddicts import (
    generic_typeddicts,
    simple_typeddicts,
    simple_typeddicts_with_extra_keys,
)


def mk_converter(detailed_validation: bool = True) -> Converter:
    """We can't use function-scoped fixtures with Hypothesis strats."""
    c = Converter(detailed_validation=detailed_validation)
    c.register_unstructure_hook(datetime, lambda d: d.timestamp())
    c.register_structure_hook(datetime, lambda d, _: datetime.fromtimestamp(d))
    return c


def get_annot(t) -> dict:
    """Our version, handling type vars properly."""
    if is_generic(t):
        # This will have typevars.
        origin = getattr(t, "__origin__", None)
        if origin is not None:
            origin_annotations = get_annotations(origin)
            args = t.__args__
            params = origin.__parameters__
            param_to_args = dict(zip(params, args))
            return {
                k: param_to_args[v] if v in param_to_args else v
                for k, v in origin_annotations.items()
            }
        else:
            # Origin is `None`, so this is a subclass for a generic typeddict.
            mapping = generate_mapping(t)
            return {
                k: mapping[v.__name__] if v.__name__ in mapping else v
                for k, v in get_annotations(t).items()
            }
    return get_annotations(t)


@given(simple_typeddicts())
def test_simple_roundtrip(cls_and_instance) -> None:
    """Round-trips for simple classes work."""
    c = mk_converter()
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)

    if all(a is not datetime for _, a in get_annot(cls).items()):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@given(simple_typeddicts(total=False), booleans())
def test_simple_nontotal(cls_and_instance, detailed_validation: bool) -> None:
    """Non-total dicts work."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)

    if all(a is not datetime for _, a in get_annot(cls).items()):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@given(simple_typeddicts())
def test_int_override(cls_and_instance) -> None:
    """Overriding a base unstructure handler should work."""
    cls, instance = cls_and_instance

    assume(any(a is int for _, a in get_annot(cls).items()))
    assume(all(a is not datetime for _, a in get_annot(cls).items()))

    c = mk_converter()
    c.register_unstructure_hook(int, lambda i: i)
    unstructured = c.unstructure(instance, unstructure_as=cls)

    assert unstructured is not instance
    assert unstructured == instance


@given(simple_typeddicts_with_extra_keys(), booleans())
def test_extra_keys(
    cls_instance_extra: tuple[type, dict, set[str]], detailed_validation: bool
) -> None:
    """Extra keys are preserved."""
    cls, instance, extra = cls_instance_extra

    c = mk_converter(detailed_validation)

    unstructured = c.unstructure(instance, unstructure_as=cls)
    for k in extra:
        assert k in unstructured

    structured = c.structure(unstructured, cls)

    for k in extra:
        assert k in structured

    assert structured == instance


@given(generic_typeddicts(total=True), booleans())
def test_generics(
    cls_and_instance: tuple[type, dict], detailed_validation: bool
) -> None:
    """Generic TypedDicts work."""
    c = mk_converter(detailed_validation=detailed_validation)
    cls, instance = cls_and_instance

    unstructured = c.unstructure(instance, unstructure_as=cls)

    if all(a is not datetime for _, a in get_annot(cls).items()):
        assert unstructured == instance

    if all(a is int for _, a in get_annot(cls).items()):
        assert unstructured is instance

    restructured = c.structure(unstructured, cls)

    assert restructured is not unstructured
    assert restructured == instance


@given(generic_typeddicts(total=True), booleans())
def test_not_required() -> None:
    pass
