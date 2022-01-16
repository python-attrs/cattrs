"""Tests for the extended validation mode."""
import pytest
from attrs import define, field
from attrs.validators import in_

from cattrs import GenConverter
from cattrs.errors import ClassValidationError


def test_class_validation():
    c = GenConverter(extended_validation=True)

    @define
    class Test:
        a: int
        b: str = field(validator=in_(["a", "b"]))
        c: str

    with pytest.raises(ClassValidationError) as exc:
        c.structure({"a": "a", "b": "c"}, Test)

    assert repr(exc.value.errors_by_attribute["a"]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert repr(exc.value.errors_by_attribute["c"]) == repr(KeyError("c"))
