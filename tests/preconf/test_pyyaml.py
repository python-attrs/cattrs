"""Pyyaml-specific tests."""

from datetime import date, datetime, timezone

from attrs import define
from hypothesis import given
from pytest import raises

from cattrs._compat import FrozenSetSubscriptable
from cattrs.errors import ClassValidationError
from cattrs.preconf.pyyaml import make_converter

from ..test_preconf import Everything, everythings, native_unions


@given(everythings())
def test_pyyaml(everything: Everything):
    from yaml import safe_dump, safe_load

    converter = make_converter()
    unstructured = converter.unstructure(everything)
    raw = safe_dump(unstructured)
    assert converter.structure(safe_load(raw), Everything) == everything


@given(everythings())
def test_pyyaml_converter(everything: Everything):
    converter = make_converter()
    raw = converter.dumps(everything)
    assert converter.loads(raw, Everything) == everything


@given(everythings())
def test_pyyaml_converter_unstruct_collection_overrides(everything: Everything):
    converter = make_converter(
        unstruct_collection_overrides={FrozenSetSubscriptable: sorted}
    )
    raw = converter.unstructure(everything)
    assert raw["a_frozenset"] == sorted(raw["a_frozenset"])


@given(union_and_val=native_unions(), detailed_validation=...)
def test_pyyaml_unions(union_and_val: tuple, detailed_validation: bool):
    """Native union passthrough works."""
    converter = make_converter(detailed_validation=detailed_validation)
    type, val = union_and_val

    assert converter.structure(val, type) == val


@given(detailed_validation=...)
def test_pyyaml_dates(detailed_validation: bool):
    """Pyyaml dates work."""
    converter = make_converter(detailed_validation=detailed_validation)

    @define
    class A:
        datetime: datetime
        date: date

    data = """
    datetime: 1970-01-01T00:00:00Z
    date: 1970-01-01"""
    assert converter.loads(data, A) == A(
        datetime(1970, 1, 1, tzinfo=timezone.utc), date(1970, 1, 1)
    )

    bad_data = """
    datetime: 1
    date: 1
    """

    with raises(ClassValidationError if detailed_validation else Exception) as exc_info:
        converter.loads(bad_data, A)

    if detailed_validation:
        assert (
            repr(exc_info.value.exceptions[0])
            == "Exception('Expected datetime, got 1')"
        )
        assert (
            repr(exc_info.value.exceptions[1]) == "ValueError('Expected date, got 1')"
        )
