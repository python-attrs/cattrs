import pytest
from attrs import define
from pg import structure

from cattrs.constraints import Constraint
from cattrs.errors import (
    ClassValidationError,
    ConstraintError,
    ConstraintGroupError,
    IterableValidationError,
)
from cattrs.v import transform_error


@define
class A:
    a: int
    b: list[int]


def test_direct_list_constaints() -> None:
    with pytest.raises(ConstraintGroupError) as exc_info:
        structure([], list[int], lambda lst: [Constraint.nonempty(lst)])

    assert exc_info.value.cl == list[int]


def test_list_element_constraints() -> None:
    """List elements can be constrained."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            [1, 0, "a"], list[int], lambda lst: [Constraint.each(lst, is_positive)]
        )
    assert transform_error(exc_info.value) == [
        "constraint violated: too small @ $[1]",
        "invalid value for type, expected int @ $[2]",
    ]


def test_direct_attrs_constraints() -> None:
    """Direct (root) constraints work on attrs classes."""
    too_small = "too small"
    too_short = "too short"
    with pytest.raises(ConstraintGroupError) as exc_info:
        structure(
            {"a": -1, "b": []},
            A,
            lambda cl: [
                Constraint.for_(cl, lambda a: too_small if a.a < 0 else None),
                Constraint.for_(cl, lambda a: too_short if len(a.b) < 1 else None),
            ],
        )

    assert exc_info.value.cl is A
    assert len(exc_info.value.exceptions) == 2
    assert isinstance(exc_info.value.exceptions[0], ConstraintError)
    assert exc_info.value.exceptions[0].args[0] == too_small
    assert isinstance(exc_info.value.exceptions[1], ConstraintError)
    assert exc_info.value.exceptions[1].args[0] == too_short


def test_attr_field_constraints() -> None:
    """Attrs fields can be constrained."""
    too_small = "too small"
    too_short = "too short"
    with pytest.raises(ClassValidationError) as exc_info:
        structure(
            {"a": -1, "b": []},
            A,
            lambda cl: [
                Constraint.for_(cl.a, lambda a: too_small if a < 0 else None),
                Constraint.for_(cl.b, lambda b: too_short if len(b) < 1 else None),
            ],
        )

    assert transform_error(exc_info.value) == [
        f"constraint violated: {too_small} @ $.a",
        f"constraint violated: {too_short} @ $.b",
    ]
