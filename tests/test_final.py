from attrs import Factory, define

from cattrs import Converter
from cattrs._compat import Final


@define
class C:
    a: Final[int]


def test_unstructure_final(genconverter: Converter) -> None:
    """Unstructuring should work, and unstructure hooks should work."""
    assert genconverter.unstructure(C(1)) == {"a": 1}

    genconverter.register_unstructure_hook(int, lambda i: str(i))
    assert genconverter.unstructure(C(1)) == {"a": "1"}


def test_structure_final(genconverter: Converter) -> None:
    """Structuring should work, and structure hooks should work."""
    assert genconverter.structure({"a": 1}, C) == C(1)

    genconverter.register_structure_hook(int, lambda i, _: int(i) + 1)
    assert genconverter.structure({"a": "1"}, C) == C(2)


@define
class D:
    a: Final[int]
    b: Final = 5
    c: Final = Factory(lambda: 3)


def test_unstructure_bare_final(genconverter: Converter) -> None:
    """Unstructuring bare Finals should work, and unstructure hooks should work."""
    assert genconverter.unstructure(D(1)) == {"a": 1, "b": 5, "c": 3}

    genconverter.register_unstructure_hook(int, lambda i: str(i))
    # Bare finals resolve to `Final[Any]`, so the custom hook works.
    assert genconverter.unstructure(D(1)) == {"a": "1", "b": "5", "c": "3"}


def test_structure_bare_final(genconverter: Converter) -> None:
    """Structuring should work, and structure hooks should work."""
    assert genconverter.structure({"a": 1, "b": 3}, D) == D(1, 3)

    genconverter.register_structure_hook(int, lambda i, _: int(i) + 1)
    assert genconverter.structure({"a": "1", "b": "3"}, D) == D(2, 4, 3)
