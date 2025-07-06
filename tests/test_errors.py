import pickle
from pathlib import Path
from typing import Any

import pytest

from cattrs._compat import ExceptionGroup
from cattrs.errors import (
    BaseValidationError,
    ClassValidationError,
    ForbiddenExtraKeysError,
    IterableValidationError,
    StructureHandlerNotFoundError,
)


@pytest.mark.parametrize(
    "err_cls, err_args",
    [
        (StructureHandlerNotFoundError, ("Structure Message", int)),
        (ForbiddenExtraKeysError, ("Forbidden Message", int, {"foo", "bar"})),
        (ForbiddenExtraKeysError, ("", str, {"foo", "bar"})),
        (ForbiddenExtraKeysError, (None, list, {"foo", "bar"})),
        (
            BaseValidationError,
            ("BaseValidation Message", [ValueError("Test BaseValidation")], int),
        ),
        (
            IterableValidationError,
            ("IterableValidation Msg", [ValueError("Test IterableValidation")], int),
        ),
        (
            ClassValidationError,
            ("ClassValidation Message", [ValueError("Test ClassValidation")], int),
        ),
    ],
)
def test_errors_pickling(
    err_cls: type[Exception], err_args: tuple[Any, ...], tmp_path: Path
) -> None:
    """Test if a round of pickling and unpickling works for errors."""
    before = err_cls(*err_args)

    assert before.args == err_args
    after = pickle.loads(pickle.dumps(before))  # noqa: S301

    assert isinstance(after, err_cls)

    assert str(after) == str(before)

    if issubclass(err_cls, ExceptionGroup):
        assert after.message == before.message
        assert after.args[0] == before.args[0]

        # We need to do the exceptions within the group (i.e. args[1])
        # separately, as on unpickling new objects are created and hence
        # they will never be equal to the original ones.
        for after_exc, before_exc in zip(after.exceptions, before.exceptions):
            assert str(after_exc) == str(before_exc)

        # The problem with args[1] might be also for other parameters, but
        # we ignore this here and if needed then we need a separate test
        assert after.args[2:] == before.args[2:]

    else:
        assert after.args == err_args
        assert after.args == before.args

    assert after.__cause__ == before.__cause__
    assert after.__context__ == before.__context__
    assert after.__traceback__ == before.__traceback__
