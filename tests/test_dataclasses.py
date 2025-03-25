import dataclasses
from typing import List

import attr
import pytest

from cattrs import BaseConverter

from ._compat import is_py310_plus


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


@pytest.mark.skipif(not is_py310_plus, reason="kwonly fields are Python 3.10+")
def test_kw_only_propagation(converter: BaseConverter):
    """KW-only args work.

    Reproducer from https://github.com/python-attrs/cattrs/issues/637.
    """

    @dataclasses.dataclass
    class PartialKeywords:
        a1: str = "Default"
        a2: str = dataclasses.field(kw_only=True)

    assert converter.structure({"a2": "Value"}, PartialKeywords) == PartialKeywords(
        a1="Default", a2="Value"
    )
