import dataclasses
from typing import List

import attr
import pytest

from cattr import Converter, GenConverter


@dataclasses.dataclass
class Foo:
    bar: str


@attr.define
class Container:
    foos: List[Foo]


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_dataclasses_in_attrs(converter_cls):
    struct = Container(
        [
            Foo("bar"),
        ]
    )

    unstruct = {
        "foos": [
            {"bar": "bar"},
        ]
    }

    converter = converter_cls()
    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, Container) == struct


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_dataclasses_in_container(converter_cls):
    struct = [
        Foo("bar"),
        Foo("bat"),
    ]

    unstruct = [
        {"bar": "bar"},
        {"bar": "bat"},
    ]

    converter = converter_cls()
    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, List[Foo]) == struct


@pytest.mark.parametrize("converter_cls", [GenConverter, Converter])
def test_dataclasses(converter_cls):
    struct = Foo("bar")

    unstruct = {"bar": "bar"}

    converter = converter_cls()
    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, Foo) == struct
