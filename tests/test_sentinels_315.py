"""Support for the built-in sentinels on Python 3.15+."""

from builtins import sentinel
from dataclasses import dataclass
from typing import Any

import pytest
from attrs import define

from cattrs import BaseConverter, Converter
from cattrs.errors import CattrsError
from cattrs.preconf.json import make_converter

MISSING = sentinel("MISSING")
UNSET = sentinel("UNSET")


def test_sentinel_roundtrip(converter: BaseConverter):
    """Sentinels serialize by name and restore the exact instance."""
    assert converter.unstructure(MISSING) == "MISSING"
    assert converter.unstructure(MISSING, MISSING) == "MISSING"
    assert converter.unstructure(MISSING, sentinel) == "MISSING"
    assert converter.structure("MISSING", MISSING) is MISSING
    assert converter.structure(["MISSING"], list[MISSING]) == [MISSING]
    assert converter.unstructure([MISSING], list[MISSING]) == ["MISSING"]


@pytest.mark.parametrize("value", ["UNSET", None, 1, [], {}, MISSING])
def test_sentinel_validation(converter: BaseConverter, value):
    """A sentinel annotation accepts only its serialized name."""
    with pytest.raises(CattrsError):
        converter.structure(value, MISSING)


@pytest.mark.parametrize("target", [int | MISSING, MISSING | int])
def test_sentinel_union(converter: BaseConverter, target):
    """Sentinel unions recognize names and convert their other members."""
    assert converter.structure("MISSING", target) is MISSING
    assert converter.structure("1", target) == 1
    assert converter.unstructure(MISSING, target) == "MISSING"
    assert converter.unstructure(1, target) == 1


@pytest.mark.parametrize("target", [MISSING | UNSET, MISSING | UNSET | None])
def test_sentinel_only_union(converter: BaseConverter, target):
    """Unions of sentinels restore each distinct singleton."""
    assert converter.structure("MISSING", target) is MISSING
    assert converter.structure("UNSET", target) is UNSET
    with pytest.raises(CattrsError):
        converter.structure([], target)


@pytest.mark.parametrize("target", [MISSING | None, int | MISSING | UNSET | None])
def test_optional_sentinel(converter: BaseConverter, target):
    """Sentinel unions also preserve None."""
    assert converter.structure(None, target) is None
    assert converter.structure("MISSING", target) is MISSING
    assert converter.unstructure(None, target) is None
    assert converter.unstructure(MISSING, target) == "MISSING"


@pytest.mark.parametrize("other", [str, Any])
def test_sentinel_name_precedence(converter: BaseConverter, other):
    """Sentinel names take precedence over strings and Any in unions."""
    assert converter.structure("MISSING", MISSING | other) is MISSING
    assert converter.structure("other", MISSING | other) == "other"


def test_duplicate_names(converter: BaseConverter):
    """Sentinels with identical names cannot be distinguished in a union."""
    duplicate = sentinel("MISSING")
    assert converter.structure("MISSING", duplicate) is duplicate
    with pytest.raises(ValueError, match="distinct names"):
        converter.get_structure_hook(MISSING | duplicate)


@pytest.mark.parametrize("decorator", [define, dataclass])
def test_sentinel_fields(converter: BaseConverter, decorator):
    """Sentinel fields and defaults roundtrip in attrs and dataclasses."""

    @decorator
    class Example:
        value: int | MISSING = MISSING

    assert converter.structure({}, Example).value is MISSING
    assert converter.structure({"value": "MISSING"}, Example).value is MISSING
    assert converter.structure({"value": "2"}, Example).value == 2
    assert converter.unstructure(Example()) == {"value": "MISSING"}


def test_omit_sentinel_default():
    """The existing omit-if-default option works with sentinel defaults."""

    @define
    class Example:
        value: int | MISSING = MISSING

    converter = Converter(omit_if_default=True)
    assert converter.unstructure(Example()) == {}
    assert converter.structure({}, Example).value is MISSING


def test_sentinel_hooks(converter: BaseConverter):
    """Per-sentinel hooks can override serialization and survive copying."""
    converter.register_unstructure_hook(MISSING, lambda _: "custom")
    converter.register_structure_hook(MISSING, lambda value, _: MISSING)
    for current in (converter, converter.copy()):
        assert current.unstructure(MISSING) == "custom"
        assert current.unstructure(MISSING, int | MISSING) == "custom"
        assert current.structure("custom", MISSING) is MISSING
        assert current.unstructure(UNSET) == "UNSET"


def test_json_sentinels():
    """Preconfigured JSON converters roundtrip sentinel fields."""

    @define
    class Example:
        value: int | MISSING = MISSING

    converter = make_converter()
    assert converter.loads(converter.dumps(Example()), Example).value is MISSING
    assert converter.loads(converter.dumps(Example(1)), Example).value == 1


def test_sentinel_runtime_dispatch(converter: BaseConverter):
    """Runtime sentinel dispatch honors hook changes and converter copy isolation."""
    assert converter.unstructure(MISSING) == "MISSING"
    converter.register_unstructure_hook(MISSING, lambda _: "original")
    assert converter.unstructure(MISSING) == "original"
    copied = converter.copy()
    copied.register_unstructure_hook(MISSING, lambda _: "copy")
    for current, expected in ((converter, "original"), (copied, "copy")):
        assert current.unstructure(MISSING) == expected
        assert current.unstructure(MISSING, sentinel) == expected
        assert current.unstructure(MISSING, int | MISSING) == expected
        assert current.unstructure([MISSING]) == [expected]
        assert current.unstructure({"value": MISSING}) == {"value": expected}


@pytest.mark.parametrize("target", [str | MISSING, str | int | MISSING | None])
def test_json_sentinel_name_precedence(target):
    """JSON union passthrough preserves sentinel name precedence."""
    converter = make_converter()
    assert converter.structure("MISSING", target) is MISSING
    assert converter.structure("other", target) == "other"
