import pytest
from attrs import define
from pg import Constraint, ConstraintError, ConstraintGroupError, structure


@define
class A:
    a: int
    b: list[int]


def test_list_constaints() -> None:
    with pytest.raises(ConstraintGroupError) as exc_info:
        structure([], list[int], lambda lst: [Constraint.nonempty(lst)])

    assert exc_info.value.cl == list[int]


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


def test_attr_field_constrains() -> None:
    """Attrs fields can be constrained."""
    too_small = "too small"
    too_short = "too short"
    with pytest.raises(ConstraintGroupError) as exc_info:
        structure(
            {"a": -1, "b": []},
            A,
            lambda cl: [
                Constraint.for_(cl.a, lambda a: too_small if a < 0 else None),
                Constraint.for_(cl.b, lambda b: too_short if len(b) < 1 else None),
            ],
        )
