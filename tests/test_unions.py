from typing import Union

import pytest
from attrs import define

from cattrs.converters import BaseConverter, Converter

from ._compat import is_py310_plus


@pytest.mark.parametrize("cls", (BaseConverter, Converter))
def test_custom_union_toplevel_roundtrip(cls: type[BaseConverter]):
    """
    Test custom code union handling.

    We override union unstructuring to add the class type, and union structuring
    to use the class type.
    """
    c = cls()

    @define
    class A:
        a: int

    @define
    class B:
        a: int

    c.register_unstructure_hook(
        Union[A, B], lambda o: {"_type": o.__class__.__name__, **c.unstructure(o)}
    )
    c.register_structure_hook(
        Union[A, B], lambda o, t: c.structure(o, A if o["_type"] == "A" else B)
    )

    inst = B(1)
    unstructured = c.unstructure(inst, unstructure_as=Union[A, B])
    assert unstructured["_type"] == "B"

    assert c.structure(unstructured, Union[A, B]) == inst


@pytest.mark.skipif(not is_py310_plus, reason="3.10 union syntax")
@pytest.mark.parametrize("cls", (BaseConverter, Converter))
def test_310_custom_union_toplevel_roundtrip(cls: type[BaseConverter]):
    """
    Test custom code union handling.

    We override union unstructuring to add the class type, and union structuring
    to use the class type.
    """
    c = cls()

    @define
    class A:
        a: int

    @define
    class B:
        a: int

    c.register_unstructure_hook(
        A | B, lambda o: {"_type": o.__class__.__name__, **c.unstructure(o)}
    )
    c.register_structure_hook(
        A | B, lambda o, t: c.structure(o, A if o["_type"] == "A" else B)
    )

    inst = B(1)
    unstructured = c.unstructure(inst, unstructure_as=A | B)
    assert unstructured["_type"] == "B"

    assert c.structure(unstructured, A | B) == inst


@pytest.mark.parametrize("cls", (BaseConverter, Converter))
def test_custom_union_clsfield_roundtrip(cls: type[BaseConverter]):
    """
    Test custom code union handling.

    We override union unstructuring to add the class type, and union structuring
    to use the class type.
    """
    c = cls()

    @define
    class A:
        a: int

    @define
    class B:
        a: int

    @define
    class C:
        f: Union[A, B]

    c.register_unstructure_hook(
        Union[A, B], lambda o: {"_type": o.__class__.__name__, **c.unstructure(o)}
    )
    c.register_structure_hook(
        Union[A, B], lambda o, t: c.structure(o, A if o["_type"] == "A" else B)
    )

    inst = C(A(1))
    unstructured = c.unstructure(inst)
    assert unstructured["f"]["_type"] == "A"

    assert c.structure(unstructured, C) == inst
