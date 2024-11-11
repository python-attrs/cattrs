from enum import Enum
from typing import Literal

from cattrs import BaseConverter
from cattrs.fns import identity


class AnEnum(Enum):
    TEST = "test"


def test_unstructure_literal(converter: BaseConverter):
    """Literals without enums are passed through by default."""
    assert converter.get_unstructure_hook(1, Literal[1]) == identity


def test_unstructure_literal_with_enum(converter: BaseConverter):
    """Literals with enums are properly unstructured."""
    assert converter.unstructure(AnEnum.TEST, Literal[AnEnum.TEST]) == "test"
