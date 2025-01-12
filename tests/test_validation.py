"""Tests for the extended validation mode."""

import pickle
from typing import Deque, Dict, FrozenSet, List, Set, Tuple

import pytest
from attrs import define, field
from attrs.validators import in_
from hypothesis import given

from cattrs import Converter
from cattrs._compat import Counter
from cattrs.errors import (
    AttributeValidationNote,
    ClassValidationError,
    IterableValidationError,
    IterableValidationNote,
)


def test_class_validation():
    """Proper class validation errors are raised when structuring."""
    c = Converter(detailed_validation=True)

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
    assert exc.value.exceptions[0].__notes__ == [
        "Structuring class test_class_validation.<locals>.Test @ attribute a"
    ]

    assert repr(exc.value.exceptions[1]) == repr(KeyError("c"))
    assert exc.value.exceptions[1].__notes__ == [
        "Structuring class test_class_validation.<locals>.Test @ attribute c"
    ]


def test_external_class_validation():
    """Proper class validation errors are raised when a classes __init__ raises."""
    c = Converter(detailed_validation=True)

    @define
    class Test:
        a: int
        b: str = field(validator=in_(["a", "b"]))
        c: str

    with pytest.raises(ClassValidationError) as exc:
        c.structure({"a": 1, "b": "c", "c": "1"}, Test)

    assert type(exc.value.exceptions[0]) is ValueError
    assert str(exc.value.exceptions[0].args[0]) == "'b' must be in ['a', 'b'] (got 'c')"


def test_list_validation():
    """Proper validation errors are raised structuring lists."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a", 3.0, "c"], List[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == [
        "Structuring typing.List[int] @ index 2"
    ]

    assert repr(exc.value.exceptions[1]) == repr(
        ValueError("invalid literal for int() with base 10: 'c'")
    )
    assert exc.value.exceptions[1].__notes__ == [
        "Structuring typing.List[int] @ index 4"
    ]


def test_deque_validation():
    """Proper validation errors are raised structuring deques."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a", 3.0, "c"], Deque[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == [
        "Structuring typing.Deque[int] @ index 2"
    ]

    assert repr(exc.value.exceptions[1]) == repr(
        ValueError("invalid literal for int() with base 10: 'c'")
    )
    assert exc.value.exceptions[1].__notes__ == [
        "Structuring typing.Deque[int] @ index 4"
    ]


def test_mapping_validation(converter):
    """Proper validation errors are raised structuring mappings."""

    if converter.detailed_validation:
        with pytest.raises(IterableValidationError) as exc:
            converter.structure({"1": 1, "2": "b", "c": 3}, Dict[int, int])

        assert repr(exc.value.exceptions[0]) == repr(
            ValueError("invalid literal for int() with base 10: 'b'")
        )
        assert exc.value.exceptions[0].__notes__ == [
            "Structuring mapping value @ key '2'"
        ]

        assert repr(exc.value.exceptions[1]) == repr(
            ValueError("invalid literal for int() with base 10: 'c'")
        )
        assert exc.value.exceptions[1].__notes__ == [
            "Structuring mapping key @ key 'c'"
        ]
    else:
        with pytest.raises(ValueError):
            converter.structure({"1": 1, "2": "b", "c": 3}, Dict[int, int])


@given(...)
def test_counter_validation(detailed_validation: bool):
    """Proper validation errors are raised structuring counters."""
    c = Converter(detailed_validation=detailed_validation)

    if detailed_validation:
        with pytest.raises(IterableValidationError) as exc:
            c.structure({"a": 1, "b": "b", "c": 3}, Counter[str])

        assert repr(exc.value.exceptions[0]) == repr(
            ValueError("invalid literal for int() with base 10: 'b'")
        )
        assert exc.value.exceptions[0].__notes__ == [
            "Structuring mapping value @ key 'b'"
        ]

    else:
        with pytest.raises(ValueError):
            c.structure({"1": 1, "2": "b", "c": 3}, Counter[str])


def test_set_validation():
    """Proper validation errors are raised structuring sets."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure({"1", 2, "a"}, Set[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == ["Structuring set @ element 'a'"]


def test_frozenset_validation():
    """Proper validation errors are raised structuring frozensets."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure({"1", 2, "a"}, FrozenSet[int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == ["Structuring frozenset @ element 'a'"]


def test_homo_tuple_validation():
    """Proper validation errors are raised structuring homogenous tuples."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a"], Tuple[int, ...])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == [
        "Structuring typing.Tuple[int, ...] @ index 2"
    ]


def test_hetero_tuple_validation():
    """Proper validation errors are raised structuring heterogenous tuples."""
    c = Converter(detailed_validation=True)

    with pytest.raises(IterableValidationError) as exc:
        c.structure(["1", 2, "a"], Tuple[int, int, int])

    assert repr(exc.value.exceptions[0]) == repr(
        ValueError("invalid literal for int() with base 10: 'a'")
    )
    assert exc.value.exceptions[0].__notes__ == [
        "Structuring typing.Tuple[int, int, int] @ index 2"
    ]


def test_notes_pickling():
    """Validation notes should be picklable"""
    note = pickle.loads(  # noqa: S301
        pickle.dumps(IterableValidationNote("foo", "key", str))
    )
    assert note == "foo"
    assert note.index == "key"
    assert note.type is str

    note = pickle.loads(  # noqa: S301
        pickle.dumps(AttributeValidationNote("foo", "name", int))
    )
    assert note == "foo"
    assert note.name == "name"
    assert note.type is int


def test_error_derive():
    """Our ExceptionGroups should derive properly."""
    c = Converter(detailed_validation=True)

    @define
    class Test:
        a: int
        b: str = field(validator=in_(["a", "b"]))
        c: str

    with pytest.raises(ClassValidationError) as exc:
        c.structure({"a": "a", "b": "c"}, Test)

    match, rest = exc.value.split(KeyError)

    assert len(match.exceptions) == 1
    assert len(rest.exceptions) == 1

    assert match.cl == exc.value.cl
    assert rest.cl == exc.value.cl


def test_iterable_note_grouping():
    """IterableValidationErrors can group their subexceptions by notes."""
    exc1 = ValueError()
    exc2 = KeyError()
    exc3 = TypeError()

    exc2.__notes__ = [note := IterableValidationNote("Test Note", 0, int)]
    exc3.__notes__ = ["A string note"]

    exc = IterableValidationError("Test", [exc1, exc2, exc3], list[int])

    with_notes, without_notes = exc.group_exceptions()

    assert with_notes == [(exc2, note)]
    assert without_notes == [exc1, exc3]


def test_class_note_grouping():
    """ClassValidationErrors can group their subexceptions by notes."""
    exc1 = ValueError()
    exc2 = KeyError()
    exc3 = TypeError()

    exc2.__notes__ = [note := AttributeValidationNote("Test Note", "a", int)]
    exc3.__notes__ = ["A string note"]

    exc = ClassValidationError("Test", [exc1, exc2, exc3], int)

    with_notes, without_notes = exc.group_exceptions()

    assert with_notes == [(exc2, note)]
    assert without_notes == [exc1, exc3]
