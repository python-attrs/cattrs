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


def test_type_alias_dedicated_hook_in_passthrough_union(converter: BaseConverter) -> None:
    """A dedicated structure hook on a PEP 695 alias runs inside a passthrough union."""
    type Trimmed = str

    configure_union_passthrough(str | int, converter)
    converter.register_structure_hook_func(
        lambda t: t is Trimmed, lambda v, _: v.strip()
    )

    assert converter.structure("  x  ", Trimmed) == "x"
    assert converter.structure("  x  ", Trimmed | int) == "x"
    assert converter.structure(1, Trimmed | int) == 1
