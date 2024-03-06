import itertools
from typing import Union

import pytest
from attrs import define
from hypothesis import given
from hypothesis.strategies import integers

from cattrs import BaseConverter
from cattrs.strategies import use_class_methods


@define
class Base:
    a: int


class Structure(Base):
    @classmethod
    def _structure(cls, data: dict):
        return cls(data["b"])  # expecting "b", not "a"


class Unstructure(Base):
    def _unstructure(self):
        return {"c": self.a}  # unstructuring as "c", not "a"


class Both(Structure, Unstructure):
    pass


@pytest.fixture
def get_converter(converter: BaseConverter):
    def aux(structure: str, unstructure: str) -> BaseConverter:
        use_class_methods(converter, structure, unstructure)
        return converter

    return aux


@pytest.mark.parametrize(
    "cls,structure_method,unstructure_method",
    itertools.product(
        [Structure, Unstructure, Both],
        ["_structure", "_undefined", None],
        ["_unstructure", "_undefined", None],
    ),
)
def test_not_nested(get_converter, structure_method, unstructure_method, cls) -> None:
    converter = get_converter(structure_method, unstructure_method)

    assert converter.structure(
        {
            (
                "b"
                if structure_method == "_structure" and hasattr(cls, "_structure")
                else "a"
            ): 42
        },
        cls,
    ) == cls(42)

    assert converter.unstructure(cls(42)) == {
        (
            "c"
            if unstructure_method == "_unstructure" and hasattr(cls, "_unstructure")
            else "a"
        ): 42
    }


@given(integers(1, 5))
def test_nested_roundtrip(depth):
    @define
    class Nested:
        a: Union["Nested", None]
        c: int

        @classmethod
        def _structure(cls, data, conv):
            b = data["b"]
            return cls(None if b is None else conv.structure(b, cls), data["c"])

        def _unstructure(self, conv):
            return {"b": conv.unstructure(self.a), "c": self.c}

        @staticmethod
        def create(depth: int) -> Union["Nested", None]:
            return None if depth == 0 else Nested(Nested.create(depth - 1), 42)

    structured = Nested.create(depth)

    converter = BaseConverter()
    use_class_methods(converter, "_structure", "_unstructure")
    assert structured == converter.structure(converter.unstructure(structured), Nested)


def test_edge_cases():
    """Test some edge cases, for coverage."""

    @define
    class Bad:
        a: int

        @classmethod
        def _structure(cls):
            """This has zero args, so can't work."""

        @classmethod
        def _unstructure(cls):
            """This has zero args, so can't work."""

    converter = BaseConverter()

    use_class_methods(converter, "_structure", "_unstructure")

    # The methods take the wrong number of args, so this should fail.
    with pytest.raises(TypeError):
        converter.structure({"a": 1}, Bad)
    with pytest.raises(TypeError):
        converter.unstructure(Bad(1))
