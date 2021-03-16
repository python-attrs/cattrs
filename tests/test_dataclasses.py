import dataclasses
from typing import List

import attr

import cattr


@dataclasses.dataclass
class Foo:
    bar: str


@attr.define
class Container:
    foos: List[Foo]


def test_dataclasses_in_attrs():
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

    assert cattr.unstructure(struct) == unstruct
    assert cattr.structure(unstruct, Container) == struct


def test_dataclasses_in_container():
    struct = [
        Foo("bar"),
        Foo("bat"),
    ]

    unstruct = [
        {"bar": "bar"},
        {"bar": "bat"},
    ]

    assert cattr.unstructure(struct) == unstruct
    assert cattr.structure(unstruct, List[Foo]) == struct


def test_dataclasses():
    struct = Foo("bar")

    unstruct = {"bar": "bar"}

    assert cattr.unstructure(struct) == unstruct
    assert cattr.structure(unstruct, Foo) == struct
