"""Tests for the fluent validation API."""
from typing import Dict, List, Union

from attrs import Factory, define, evolve
from attrs import fields as f
from pytest import fixture, raises

from cattrs import ClassValidationError, Converter
from cattrs.v import V, customize, transform_error


@fixture
def c() -> Converter:
    """We need only converters with detailed_validation=True."""
    res = Converter()

    res.register_structure_hook(
        Union[str, int], lambda v, _: v if isinstance(v, int) else str(v)
    )

    return res


@define
class Model:
    """The class we want to validate, with an assortment of fields."""

    a: int
    b: str
    c: List[str] = Factory(list)
    d: List[int] = Factory(list)
    e: Union[str, None] = None
    f: Union[int, None] = None
    g: Union[str, int] = 0
    h: Dict[str, int] = Factory(dict)


def is_lowercase(val: str) -> None:
    """A validator included with cattrs.

    Probably the simplest possible validator, only takes a string.
    """
    if val != val.lower():
        raise ValueError(f"{val!r} not lowercase")


def is_email(val: str) -> None:
    """A custom validator, not in cattrs.

    It just takes a value and maybe raises, simple as that.
    """
    if "@" not in val:
        raise ValueError(f"{val!r} is not a valid email")


def test_roundtrip(c: Converter) -> None:
    """Test models can roundtrip."""
    customize(c, Model)

    instance = Model(1, "1", ["1"], [1], "", 0, 0, {"a": 1})

    assert instance == c.structure(c.unstructure(instance), Model)


def test_omit(c: Converter) -> None:
    """Omitting a field works."""
    customize(c, Model, V(f(Model).c).omit())

    instance = Model(1, "1", ["1"], [1], "", 0, 0, {"a": 1})

    assert evolve(instance, c=[]) == c.structure(c.unstructure(instance), Model)


def test_rename(c: Converter) -> None:
    """Renaming a field works."""
    customize(c, Model, V(f(Model).c).rename("C"))

    instance = Model(1, "1", ["1"], [1], "", 0, 0, {"a": 1})

    unstructured = c.unstructure(instance)
    unstructured["C"] = unstructured["c"].pop()

    assert c.structure(unstructured, Model) == instance


def test_simple_string_validation(c: Converter) -> None:
    """Simple string validation works."""
    customize(c, Model, V(f(Model).b).ensure(is_lowercase))

    instance = Model(1, "A", ["1"], [1], "", 0, 0, {"a": 1})

    unstructured = c.unstructure(instance)

    with raises(ClassValidationError) as exc_info:
        c.structure(unstructured, Model)

    assert transform_error(exc_info.value) == [
        "invalid value ('A' not lowercase) @ $.b"
    ]

    instance.b = "a"
    assert instance == c.structure(c.unstructure(instance), Model)


def test_multiple_string_validators(c: Converter) -> None:
    """Simple string validation works."""
    customize(c, Model, V(f(Model).b).ensure(is_lowercase, is_email))

    instance = Model(1, "A", ["1"], [1], "", 0, 0, {"a": 1})

    unstructured = c.unstructure(instance)

    with raises(ClassValidationError) as exc_info:
        c.structure(unstructured, Model)

    assert transform_error(exc_info.value) == [
        "invalid value ('A' not lowercase) @ $.b",
        "invalid value ('A' is not a valid email) @ $.b",
    ]

    instance.b = "a@b"
    assert instance == c.structure(c.unstructure(instance), Model)
