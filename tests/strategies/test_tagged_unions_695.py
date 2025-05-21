import pytest

from cattrs import BaseConverter
from cattrs.strategies import configure_tagged_union

from .._compat import is_py312_plus
from .test_tagged_unions import A, B


@pytest.mark.skipif(not is_py312_plus, reason="New type alias syntax")
def test_type_alias(converter: BaseConverter):
    """Type aliases to unions also work."""
    type AOrB = A | B

    configure_tagged_union(AOrB, converter)

    assert converter.unstructure(A(1), AOrB) == {"_type": "A", "a": 1}
    assert converter.unstructure(B("1"), AOrB) == {"_type": "B", "a": "1"}

    assert converter.structure({"_type": "A", "a": 1}, AOrB) == A(1)
    assert converter.structure({"_type": "B", "a": 1}, AOrB) == B("1")
