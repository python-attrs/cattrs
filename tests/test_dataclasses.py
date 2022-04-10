import dataclasses
from typing import List

import attr

from cattrs import BaseConverter


@dataclasses.dataclass
class Foo:
    bar: str


@attr.define
class Container:
    foos: List[Foo]


def test_dataclasses_in_attrs(converter: BaseConverter):
    struct = Container([Foo("bar")])

    unstruct = {"foos": [{"bar": "bar"}]}

    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, Container) == struct


def test_dataclasses_in_container(converter: BaseConverter):
    struct = [Foo("bar"), Foo("bat")]

    unstruct = [{"bar": "bar"}, {"bar": "bat"}]

    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, List[Foo]) == struct


def test_dataclasses(converter: BaseConverter):
    struct = Foo("bar")

    unstruct = {"bar": "bar"}

    assert converter.unstructure(struct) == unstruct
    assert converter.structure(unstruct, Foo) == struct
