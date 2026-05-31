from dataclasses import dataclass

from cattrs import BaseConverter
from cattrs.strategies import configure_union_passthrough


@dataclass
class DataClass:
    field: str


def test_type_alias_union_member(converter: BaseConverter) -> None:
    """Native union passthrough handles PEP 695 aliases in the exact union."""
    type NewScalar = str

    configure_union_passthrough(str | int, converter)

    assert converter.structure("value", NewScalar | DataClass) == "value"
    assert converter.structure({"field": "value"}, NewScalar | DataClass) == DataClass(
        "value"
    )
