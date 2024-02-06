"""Tests for `cattrs.v.ensure`."""
import sys
from typing import Dict, List, MutableSequence, Sequence

from pytest import fixture, mark, raises

from cattrs import BaseConverter
from cattrs._compat import ExceptionGroup
from cattrs.errors import IterableValidationError
from cattrs.v import ensure
from cattrs.v._hooks import is_validated, validator_factory


@fixture
def valconv(converter) -> BaseConverter:
    converter.register_structure_hook_factory(is_validated, validator_factory)
    return converter


def test_ensured_ints(valconv: BaseConverter):
    """Validation for primitives works."""
    assert valconv.structure("5", ensure(int, lambda i: i > 0))

    with raises(Exception) as exc:
        valconv.structure("-5", ensure(int, lambda i: i > 0))

    if valconv.detailed_validation:
        assert isinstance(exc.value, ExceptionGroup)
        assert isinstance(exc.value.exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)


def test_ensured_lists(valconv: BaseConverter):
    """Validation for lists works."""
    assert valconv.structure([1, 2], ensure(List[int], lambda lst: len(lst) > 0))

    with raises(Exception) as exc:
        valconv.structure([], ensure(List[int], lambda lst: len(lst) > 0))

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)


@mark.parametrize("type", [List, Sequence, MutableSequence])
def test_ensured_list_elements(valconv: BaseConverter, type):
    """Validation for list elements works."""
    assert valconv.structure([1, 2], ensure(type, elems=ensure(int, lambda i: i > 0)))

    with raises(Exception) as exc:
        valconv.structure([1, -2], ensure(type, elems=ensure(int, lambda i: i > 0)))

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ExceptionGroup)
        assert isinstance(exc.value.exceptions[0].exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)

    # Now both elements and the list itself.
    assert valconv.structure(
        [1, 2],
        ensure(type, lambda lst: len(lst) < 3, elems=ensure(int, lambda i: i > 0)),
    )

    with raises(Exception) as exc:
        valconv.structure(
            [1, 2, 3],
            ensure(type, lambda lst: len(lst) < 3, elems=ensure(int, lambda i: i > 0)),
        )

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)

    with raises(Exception) as exc:
        valconv.structure(
            [1, -2],
            ensure(type, lambda lst: len(lst) < 3, elems=ensure(int, lambda i: i > 0)),
        )

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ExceptionGroup)
        assert isinstance(exc.value.exceptions[0].exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)


def test_ensured_typing_list(valconv: BaseConverter):
    """Ensure works for typing lists."""
    assert valconv.structure([1, 2], ensure(List, elems=ensure(int, lambda i: i > 0)))

    with raises(Exception) as exc:
        valconv.structure([1, -2], ensure(List, elems=ensure(int, lambda i: i > 0)))

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ExceptionGroup)
        assert isinstance(exc.value.exceptions[0].exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)


@mark.skipif(sys.version_info[:2] < (3, 10), reason="Not supported on older Pythons")
def test_ensured_list(valconv: BaseConverter):
    """Ensure works for builtin lists."""
    assert valconv.structure([1, 2], ensure(list, elems=ensure(int, lambda i: i > 0)))

    with raises(Exception) as exc:
        valconv.structure([1, -2], ensure(list, elems=ensure(int, lambda i: i > 0)))

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ExceptionGroup)
        assert isinstance(exc.value.exceptions[0].exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)


def test_ensured_typing_dict(valconv: BaseConverter):
    """Ensure works for typing.Dicts."""
    assert valconv.structure(
        {"a": 1}, ensure(Dict, lambda d: len(d) > 0, keys=str, values=int)
    )

    with raises(Exception) as exc:
        valconv.structure({}, ensure(Dict, lambda d: len(d) > 0, keys=str, values=int))

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)

    with raises(Exception) as exc:
        valconv.structure(
            {"b": 1, "c": "a"},
            ensure(Dict, keys=ensure(str, lambda s: s.startswith("a")), values=int),
        )

    if valconv.detailed_validation:
        assert isinstance(exc.value, IterableValidationError)
        assert isinstance(exc.value.exceptions[0], ExceptionGroup)
        assert isinstance(exc.value.exceptions[0].exceptions[0], ValueError)
    else:
        assert isinstance(exc.value, ValueError)
