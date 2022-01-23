"""Tests for the extended validation mode."""
from typing import Dict, FrozenSet, List, Set, Tuple

import pytest
from attrs import define, field
from attrs.validators import in_

from cattrs import GenConverter
from cattrs.errors import ClassValidationError, IterableValidationError


def test_class_validation():
    """Proper class validation errors are raised when structuring."""
    c = GenConverter(extended_validation=True)

    @define
    class Test:
        a: int
        b: str = field(validator=in_(["a", "b"]))
        c: str

    with pytest.raises(ClassValidationError) as exc:
        c.structure({"a": "a", "b": "c"}, Test)

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring class @ attribute a"

    assert repr(exc.value.exceptions[1]) == repr(KeyError("c"))
    assert exc.value.exceptions[1].__note__ == "Structuring class @ attribute c"


def test_list_validation():
    """Proper validation errors are raised structuring lists."""
    c = GenConverter(extended_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a", 3.0, "c"], List[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring iterable @ index 2"

    assert repr(exc.value.exceptions[1]) == repr(
        ValueError("invalid literal for int() with base 10: 'c'")
    )
    assert exc.value.exceptions[1].__note__ == "Structuring iterable @ index 4"


def test_mapping_validation():
    """Proper validation errors are raised structuring mappings."""
    c = GenConverter(extended_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure({"1": 1, "2": "b", "c": 3}, Dict[int, int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'b'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring mapping value @ key '2'"

    assert repr(exc.value.exceptions[1]) == repr(
        ValueError("invalid literal for int() with base 10: 'c'")
    )
    assert exc.value.exceptions[1].__note__ == "Structuring mapping key @ key 'c'"


def test_set_validation():
    """Proper validation errors are raised structuring sets."""
    c = GenConverter(extended_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure({"1", 2, "a"}, Set[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring set @ element 'a'"


def test_frozenset_validation():
    """Proper validation errors are raised structuring frozensets."""
    c = GenConverter(extended_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure({"1", 2, "a"}, FrozenSet[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring frozenset @ element 'a'"


def test_homo_tuple_validation():
    """Proper validation errors are raised structuring homogenous tuples."""
    c = GenConverter(extended_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a"], Tuple[int, ...])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__note__ == "Structuring tuple @ index 2"
