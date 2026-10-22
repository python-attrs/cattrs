"""Mapping keys remain strings after their configured unstructure hooks."""

from base64 import b85encode
from enum import Enum
from typing import Any, Union

import pytest
from attrs import define

orjson = pytest.importorskip("orjson")
make_converter = pytest.importorskip("cattrs.preconf.orjson").make_converter


@pytest.mark.parametrize("detailed_validation", [True, False])
@pytest.mark.parametrize("key_type", [Union[str, int], str | int, Any, int])
def test_mapping_keys_are_stringified(key_type, detailed_validation):
    converter = make_converter(detailed_validation=detailed_validation)
    data = {1: 7} if key_type is int else {1: 7, "second": 9}
    expected = {str(key): value for key, value in data.items()}
    target = dict[key_type, int]
    assert converter.unstructure(data, unstructure_as=target) == expected
    assert orjson.loads(converter.dumps(data, unstructure_as=target)) == expected


def test_union_mapping_in_attrs_field():
    @define
    class Record:
        entries: dict[Union[str, int], int]

    converter = make_converter()
    assert orjson.loads(converter.dumps(Record({1: 7}))) == {"entries": {"1": 7}}


def test_string_enum_keys_keep_values():
    class Key(str, Enum):
        FIRST = "first"

    converter = make_converter()
    assert orjson.loads(
        converter.dumps({Key.FIRST: 7}, unstructure_as=dict[Key, int])
    ) == {"first": 7}


def test_bytes_keys_keep_base85_hook():
    converter = make_converter()
    assert orjson.loads(
        converter.dumps({b"key": 7}, unstructure_as=dict[bytes, int])
    ) == {b85encode(b"key").decode("utf8"): 7}


@pytest.mark.parametrize("hook_result", [42, "custom"])
def test_custom_key_hook_is_applied_before_stringification(hook_result):
    class Key:
        pass

    converter = make_converter()
    converter.register_unstructure_hook(Key, lambda _: hook_result)
    assert orjson.loads(converter.dumps({Key(): 7}, unstructure_as=dict[Key, int])) == {
        str(hook_result): 7
    }
