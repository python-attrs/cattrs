from collections.abc import Mapping, MutableMapping
from typing import Annotated, TypedDict

import pytest
from attrs import define
from pg import structure

from cattrs import Converter
from cattrs.constraints import Constraint, ConstraintAnnotated
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
                Constraint(cl, lambda a: too_small if a.a < 0 else None),
                Constraint(cl, lambda a: too_short if len(a.b) < 1 else None),
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
                Constraint(cl.a, lambda a: too_small if a < 0 else None),
                Constraint(cl.b, lambda b: too_short if len(b) < 1 else None),
            ],
        )

    assert transform_error(exc_info.value) == [
        f"constraint violated: {too_small} @ $.a",
        f"constraint violated: {too_short} @ $.b",
    ]


def test_dict_value_constraints() -> None:
    """Dictionary values constraints work."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    # Values check
    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {1: 0, 2: 1}, dict[int, int], lambda d: [Constraint.values(d, is_positive)]
        )

    assert "constraint violated: too small" in str(transform_error(exc_info.value))


def test_dict_item_constraints() -> None:
    """Dict item constraints work."""

    def sum_is_positive(item: tuple[int, int]) -> str | None:
        return "sum too small" if item[0] + item[1] < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {0: 0, 1: 1},  # 0+0=0 fails
            dict[int, int],
            lambda d: [Constraint.items(d, sum_is_positive)],
        )

    assert "constraint violated: sum too small" in str(transform_error(exc_info.value))


def test_dict_keys_constraints() -> None:
    """Dict keys constraints work."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {0: 1, 1: 1},  # 0 key fails
            dict[int, int],
            lambda d: [Constraint.each(d, is_positive)],
        )

    assert "constraint violated: too small" in str(transform_error(exc_info.value))


def test_mapping_constraints():
    """Mapping values constraints work."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {1: 0}, Mapping[int, int], lambda d: [Constraint.values(d, is_positive)]
        )
    assert "constraint violated: too small" in str(transform_error(exc_info.value))


def test_mutable_mapping_constraints():
    """MutableMapping values constraints work."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {1: 0},
            MutableMapping[int, int],
            lambda d: [Constraint.values(d, is_positive)],
        )
    assert "constraint violated: too small" in str(transform_error(exc_info.value))


def test_mapping_item_constraints():
    """Mapping item constraints work."""

    def sum_is_positive(item: tuple[int, int]) -> str | None:
        return "sum too small" if item[0] + item[1] < 1 else None

    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {0: 0}, Mapping[int, int], lambda d: [Constraint.items(d, sum_is_positive)]
        )
    assert "constraint violated: sum too small" in str(transform_error(exc_info.value))


def test_iter_constraints() -> None:
    """Test using iteration on validation dummy to generate constraints."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    # Test list iteration
    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            [1, 0], list[int], lambda lst: [Constraint(e, is_positive) for e in lst]
        )
    assert "constraint violated: too small" in str(transform_error(exc_info.value))

    # Test dict iteration (keys)
    with pytest.raises(IterableValidationError) as exc_info:
        structure(
            {0: 1}, dict[int, int], lambda d: [Constraint(k, is_positive) for k in d]
        )
    assert "constraint violated: too small" in str(transform_error(exc_info.value))


def test_int_constraint() -> None:
    """A simple integer constraint works."""

    def is_positive(val: int) -> str | None:
        return "too small" if val < 1 else None

    # Success
    assert structure(1, int, lambda v: [Constraint(v, is_positive)]) == 1

    # Failure
    with pytest.raises(ConstraintGroupError) as exc_info:
        structure(0, int, lambda v: [Constraint(v, is_positive)])

    assert exc_info.value.exceptions[0].args[0] == "too small"


class TD(TypedDict):
    a: int
    b: int


def test_typed_dict_constraints() -> None:
    """TypedDict fields can be constrained."""
    too_small = "too small"

    with pytest.raises(ClassValidationError) as exc_info:
        structure(
            {"a": -1, "b": 1},
            TD,
            lambda td: [Constraint(td["a"], lambda a: too_small if a < 0 else None)],
        )

    assert transform_error(exc_info.value) == [
        f"constraint violated: {too_small} @ $.a"
    ]


def test_typed_dict_constraints_no_detailed_validation() -> None:
    """TypedDict fields can be constrained without detailed validation."""
    too_small = "too small"
    converter = Converter(detailed_validation=False)

    def is_too_small(a: int) -> str | None:
        return too_small if a < 0 else None

    hooks = ((("a",), (is_too_small,)),)
    structure_as = Annotated[TD, ConstraintAnnotated(hooks)]

    # Should raise ConstraintError directly, not wrapped
    with pytest.raises(ConstraintError) as exc_info:
        converter.structure({"a": -1, "b": 1}, structure_as)

    assert exc_info.value.args[0] == too_small
